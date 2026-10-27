"""Pagamentos do pedido (fechamento): dinheiro, PIX (QR demonstrativo), débito, crédito (até 6x) e boleto (em aberto).

GET    /pedidos/{id}/pagamentos                 lista + totais (total, pago, em aberto, restante)
POST   /pedidos/{id}/pagamentos                 {forma, valor_cent, parcelas, pago, vencimento, obs}
PATCH  /pedidos/{id}/pagamentos/{pid}/pago      ?pago=true|false
DELETE /pedidos/{id}/pagamentos/{pid}
GET    /pedidos/{id}/pix-qr?valor_cent=..       PNG do QR Code (payload BR Code estático DEMONSTRATIVO — não é cobrança real)
POST   /pedidos/{id}/fechar                     exige cobertura do total -> status ENTREGUE
"""
from __future__ import annotations

import io
import uuid
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

import db
from utils.auth import requer_nivel, usuario_atual

router = APIRouter(prefix="/pedidos", tags=["pagamentos"], dependencies=[Depends(requer_nivel(2))])
FORMAS = ("DINHEIRO", "PIX", "DEBITO", "CREDITO", "BOLETO")
MAX_PARCELAS = 6


class PagamentoIn(BaseModel):
    forma: str = Field(pattern="^(DINHEIRO|PIX|DEBITO|CREDITO|BOLETO)$")
    valor_cent: int = Field(gt=0)
    parcelas: int = Field(default=1, ge=1, le=MAX_PARCELAS)
    pago: bool = True
    vencimento: Optional[date] = None
    obs: Optional[str] = Field(default=None, max_length=200)


def _pedido(con, pedido_id: int, user: dict) -> dict:
    p = db.um(con, """SELECT P.*, C.NOME CLIENTE_NOME, C.CPF_CNPJ, C.LOGRADOURO, C.CIDADE, C.CEP FROM PEDIDO P
                      JOIN CLIENTE C ON C.ID = P.CLIENTE_ID WHERE P.ID = %s AND P.EMPRESA_ID = %s""", [pedido_id, user["empresa_id"]])
    if not p:
        raise HTTPException(404, "Pedido não encontrado")
    if user.get("oficina_id") and user["oficina_id"] != p["OFICINA_ID"]:
        raise HTTPException(403, "Pedido de outra oficina")
    return p


def _resumo(con, p: dict) -> dict:
    pags = db.todos(con, """SELECT G.*, U.NOME RECEBIDO_POR_NOME FROM PAGAMENTO G LEFT JOIN USUARIO U ON U.ID = G.RECEBIDO_POR
                            WHERE G.PEDIDO_ID = %s ORDER BY G.ID""", [p["ID"]])
    pago = sum(int(x["VALOR_CENT"]) for x in pags if x["PAGO"])
    aberto = sum(int(x["VALOR_CENT"]) for x in pags if not x["PAGO"])
    total = int(p["TOTAL_CENT"])
    return {"pagamentos": pags, "total_cent": total, "pago_cent": pago, "aberto_cent": aberto,
            "restante_cent": max(total - pago - aberto, 0), "coberto": pago + aberto >= total}


@router.get("/{pedido_id}/pagamentos")
def listar(pedido_id: int, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    p = _pedido(con, pedido_id, user)
    r = _resumo(con, p)
    r["cliente"] = {"nome": p["CLIENTE_NOME"], "cpf_cnpj": p["CPF_CNPJ"], "endereco_ok": bool(p["LOGRADOURO"] and p["CIDADE"] and p["CEP"])}
    r["status"] = p["STATUS"]
    return r


@router.post("/{pedido_id}/pagamentos")
def lancar(pedido_id: int, d: PagamentoIn, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    p = _pedido(con, pedido_id, user)
    if p["TIPO"] != "PEDIDO" or p["STATUS"] in ("CANCELADO", "FATURADO"):
        raise HTTPException(409, "Só pedidos aprovados e não encerrados recebem pagamento")
    r = _resumo(con, p)
    if d.valor_cent > r["restante_cent"] + 0 and r["restante_cent"] > 0 and d.valor_cent - r["restante_cent"] > 0 and d.forma != "DINHEIRO":
        raise HTTPException(400, f"Valor acima do restante (R$ {r['restante_cent']/100:.2f}); só dinheiro aceita troco")
    if r["restante_cent"] == 0:
        raise HTTPException(409, "Pedido já está coberto")
    parcelas = d.parcelas if d.forma == "CREDITO" else 1
    pago, venc, nosso, txid = d.pago, None, None, None
    if d.forma == "BOLETO":
        if not p["CPF_CNPJ"]:
            raise HTTPException(400, "Boleto exige CPF/CNPJ do cliente — complete o cadastro")
        if not (p["LOGRADOURO"] and p["CIDADE"] and p["CEP"]):
            raise HTTPException(400, "Boleto exige endereço completo do cliente (logradouro, cidade, CEP)")
        pago = False
        venc = d.vencimento or date.today()
        nosso = f"{p['NUMERO_PEDIDO']:08d}{datetime.now():%d%m%y}"   # placeholder até a integração bancária
    if d.forma == "PIX":
        txid = uuid.uuid4().hex[:25].upper()
    valor = min(d.valor_cent, r["restante_cent"]) if d.forma == "DINHEIRO" else d.valor_cent
    novo = db.executar(con, """INSERT INTO PAGAMENTO (PEDIDO_ID, FORMA, VALOR_CENT, PARCELAS, PAGO, PAGO_EM, VENCIMENTO, NOSSO_NUMERO, TXID, RECEBIDO_POR, OBS)
                               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                      [pedido_id, d.forma, valor, parcelas, int(pago), datetime.now() if pago else None, venc, nosso, txid, int(user["sub"]),
                       (d.obs or "")[:200] or (f"troco R$ {(d.valor_cent - valor)/100:.2f}" if d.forma == "DINHEIRO" and d.valor_cent > valor else None)])
    out = _resumo(con, p); out["id"] = novo; out["troco_cent"] = d.valor_cent - valor if d.forma == "DINHEIRO" else 0
    return out


@router.patch("/{pedido_id}/pagamentos/{pag_id}/pago")
def marcar_pago(pedido_id: int, pag_id: int, pago: bool = True, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    p = _pedido(con, pedido_id, user)
    n = db.executar(con, "UPDATE PAGAMENTO SET PAGO=%s, PAGO_EM=%s, RECEBIDO_POR=%s WHERE ID=%s AND PEDIDO_ID=%s",
                    [int(pago), datetime.now() if pago else None, int(user["sub"]), pag_id, pedido_id])
    if not n:
        raise HTTPException(404, "Pagamento não encontrado")
    return _resumo(con, p)


@router.delete("/{pedido_id}/pagamentos/{pag_id}")
def excluir(pedido_id: int, pag_id: int, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    p = _pedido(con, pedido_id, user)
    if p["STATUS"] in ("ENTREGUE", "FATURADO"):
        raise HTTPException(409, "Pedido já entregue: estorno só pelo financeiro")
    db.executar(con, "DELETE FROM PAGAMENTO WHERE ID=%s AND PEDIDO_ID=%s", [pag_id, pedido_id])
    return _resumo(con, p)


def _emv(tag: str, valor: str) -> str:
    return f"{tag}{len(valor):02d}{valor}"


def _crc16(s: str) -> str:
    crc = 0xFFFF
    for ch in s.encode("utf-8"):
        crc ^= ch << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) if crc & 0x8000 else (crc << 1)
            crc &= 0xFFFF
    return f"{crc:04X}"


def payload_pix(chave: str, nome: str, cidade: str, valor_cent: int, txid: str) -> str:
    """BR Code estático (padrão EMV do Bacen). Com chave de demonstração, o banco do cliente vai recusar — é só para a tela."""
    mai = _emv("00", "br.gov.bcb.pix") + _emv("01", chave)
    s = _emv("00", "01") + _emv("26", mai) + _emv("52", "0000") + _emv("53", "986") + _emv("54", f"{valor_cent/100:.2f}") + _emv("58", "BR") \
        + _emv("59", nome[:25]) + _emv("60", cidade[:15]) + _emv("62", _emv("05", txid[:25])) + "6304"
    return s + _crc16(s)


@router.get("/{pedido_id}/pix-qr")
def pix_qr(pedido_id: int, valor_cent: int = Query(gt=0), user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    p = _pedido(con, pedido_id, user)
    emp = db.um(con, "SELECT FANTASIA, CIDADE, CNPJ FROM EMPRESA WHERE ID = %s", [user["empresa_id"]])
    txid = f"AOF{p['NUMERO_PEDIDO'] or p['NUMERO_ORCAMENTO']}{datetime.now():%H%M%S}"
    payload = payload_pix(chave="demo@aofficina.com.br", nome=emp["FANTASIA"] or "aOfficina", cidade=emp["CIDADE"] or "RIO CLARO",
                          valor_cent=valor_cent, txid=txid)
    try:
        import qrcode
        img = qrcode.make(payload, box_size=8, border=2)
        buf = io.BytesIO(); img.save(buf, format="PNG")
        return Response(buf.getvalue(), media_type="image/png", headers={"X-Pix-Payload": payload, "Cache-Control": "no-store"})
    except ImportError:
        raise HTTPException(503, "Biblioteca qrcode não instalada (pip install qrcode Pillow)")


@router.post("/{pedido_id}/fechar")
def fechar(pedido_id: int, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    """Entrega do veículo: exige pagamentos cobrindo o total (boleto em aberto conta)."""
    p = _pedido(con, pedido_id, user)
    if p["STATUS"] != "CONCLUIDO":
        raise HTTPException(409, "Conclua o pedido antes de fechar")
    r = _resumo(con, p)
    if not r["coberto"]:
        raise HTTPException(409, f"Faltam R$ {r['restante_cent']/100:.2f} para cobrir o total")
    db.executar(con, "UPDATE PEDIDO SET STATUS='ENTREGUE', ENTREGUE_EM=NOW() WHERE ID=%s", [pedido_id])
    if p["AGENDA_ID"]:
        db.executar(con, "UPDATE AGENDA SET STATUS='CONCLUIDO' WHERE ID=%s", [p["AGENDA_ID"]])
    return {"ok": True, "status": "ENTREGUE", **{k: r[k] for k in ("total_cent", "pago_cent", "aberto_cent")}}
