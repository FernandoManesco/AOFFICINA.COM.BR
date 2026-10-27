"""Orçamento -> Pedido (OS).

Ciclo:
  ORCAMENTO/ABERTO  --itens--> ORCAMENTO/ENVIADO --aprovar--> PEDIDO/APROVADO (ganha NUMERO_PEDIDO)
  PEDIDO: APROVADO -> EM_EXECUCAO -> CONCLUIDO -> ENTREGUE -> FATURADO   (ou CANCELADO)
Itens só podem ser alterados enquanto não CONCLUIDO/ENTREGUE/FATURADO/CANCELADO.
Totais sempre recalculados no servidor a partir dos itens AUTORIZADOS.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

import db
from routers.servicos import valor_previsto_cent
from utils.auth import requer_nivel, usuario_atual

router = APIRouter(prefix="/pedidos", tags=["pedidos"], dependencies=[Depends(requer_nivel(3))])

STATUS_TRAVADOS = ("CONCLUIDO", "ENTREGUE", "FATURADO", "CANCELADO")


# ---------- modelos ----------
class PedidoIn(BaseModel):
    oficina_id: int
    cliente_id: int
    veiculo_id: int
    tipo: str = Field(default="ORCAMENTO", pattern="^(ORCAMENTO|PEDIDO)$")
    agenda_id: Optional[int] = None
    funcionario_id: Optional[int] = None
    km_entrada: Optional[int] = Field(default=None, ge=0)
    guincho: bool = False
    queixa: Optional[str] = None
    diagnostico: Optional[str] = None
    observacao: Optional[str] = None
    previsao_entrega: Optional[datetime] = None
    validade_orcamento: Optional[str] = None
    desconto_cent: int = Field(default=0, ge=0)


class ServicoItemIn(BaseModel):
    servico_id: Optional[int] = None
    descricao: Optional[str] = Field(default=None, max_length=200)
    funcionario_id: Optional[int] = None
    horas: Optional[float] = Field(default=None, gt=0)
    valor_hora_cent: Optional[int] = Field(default=None, ge=0)
    valor_cent: Optional[int] = Field(default=None, ge=0)   # se informado, prevalece (valor fechado)
    autorizado: bool = True


class PecaItemIn(BaseModel):
    peca_id: Optional[int] = None
    descricao: Optional[str] = Field(default=None, max_length=200)
    quantidade: float = Field(default=1, gt=0)
    valor_unit_cent: Optional[int] = Field(default=None, ge=0)
    autorizado: bool = True


class ExecucaoIn(BaseModel):
    executado: bool = True
    descricao_executado: Optional[str] = None
    funcionario_id: Optional[int] = None


class AprovacaoIn(BaseModel):
    aprovado_por_nome: str = Field(min_length=2, max_length=100)
    funcionario_id: Optional[int] = None
    previsao_entrega: Optional[datetime] = None


# ---------- helpers ----------
def _carregar(con, pedido_id: int, user: dict) -> dict:
    p = db.um(con, "SELECT * FROM PEDIDO WHERE ID = %s AND EMPRESA_ID = %s", [pedido_id, user["empresa_id"]])
    if not p:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if user.get("oficina_id") and user["oficina_id"] != p["OFICINA_ID"]:
        raise HTTPException(status_code=403, detail="Pedido de outra oficina")
    return p


def _exigir_editavel(p: dict):
    if p["STATUS"] in STATUS_TRAVADOS:
        raise HTTPException(status_code=409, detail=f"Pedido {p['STATUS']} não pode ser alterado")


def _proximo_numero(con, empresa_id: int, nome: str) -> int:
    db.executar(con, "INSERT INTO SEQUENCIA (EMPRESA_ID, NOME, VALOR) VALUES (%s, %s, 0) "
                     "ON DUPLICATE KEY UPDATE VALOR = VALOR", [empresa_id, nome])
    row = db.um(con, "SELECT VALOR FROM SEQUENCIA WHERE EMPRESA_ID = %s AND NOME = %s FOR UPDATE", [empresa_id, nome])
    novo = int(row["VALOR"]) + 1
    db.executar(con, "UPDATE SEQUENCIA SET VALOR = %s WHERE EMPRESA_ID = %s AND NOME = %s", [novo, empresa_id, nome])
    return novo


def _recalcular(con, pedido_id: int):
    s = db.um(con, "SELECT COALESCE(SUM(VALOR_CENT),0) T FROM PEDIDO_SERVICO WHERE PEDIDO_ID = %s AND AUTORIZADO = 1", [pedido_id])
    pc = db.um(con, "SELECT COALESCE(SUM(VALOR_CENT),0) T FROM PEDIDO_PECA WHERE PEDIDO_ID = %s AND AUTORIZADO = 1", [pedido_id])
    db.executar(con, """UPDATE PEDIDO SET TOTAL_SERVICOS_CENT = %s, TOTAL_PECAS_CENT = %s,
                        TOTAL_CENT = GREATEST(%s + %s - DESCONTO_CENT, 0) WHERE ID = %s""",
                [int(s["T"]), int(pc["T"]), int(s["T"]), int(pc["T"]), pedido_id])


def _detalhe(con, pedido_id: int) -> dict:
    p = db.um(con, """SELECT P.*, C.NOME CLIENTE_NOME, C.TELEFONE CLIENTE_TELEFONE, C.WHATSAPP CLIENTE_WHATSAPP, C.CPF_CNPJ,
                             V.PLACA, V.MARCA, V.MODELO, V.ANO_FAB, V.ANO_MODELO, V.COR, V.KM_ATUAL,
                             F.NOME FUNCIONARIO_NOME, O.NOME OFICINA_NOME
                      FROM PEDIDO P JOIN CLIENTE C ON C.ID = P.CLIENTE_ID JOIN VEICULO V ON V.ID = P.VEICULO_ID
                      JOIN OFICINA O ON O.ID = P.OFICINA_ID LEFT JOIN FUNCIONARIO F ON F.ID = P.FUNCIONARIO_ID
                      WHERE P.ID = %s""", [pedido_id])
    p["servicos"] = db.todos(con, """SELECT S.*, F.NOME FUNCIONARIO_NOME, SV.CODIGO SERVICO_CODIGO FROM PEDIDO_SERVICO S
                                     LEFT JOIN FUNCIONARIO F ON F.ID = S.FUNCIONARIO_ID LEFT JOIN SERVICO SV ON SV.ID = S.SERVICO_ID
                                     WHERE S.PEDIDO_ID = %s ORDER BY S.ID""", [pedido_id])
    p["pecas"] = db.todos(con, """SELECT PP.*, PE.CODIGO PECA_CODIGO, PE.UNIDADE FROM PEDIDO_PECA PP
                                  LEFT JOIN PECA PE ON PE.ID = PP.PECA_ID WHERE PP.PEDIDO_ID = %s ORDER BY PP.ID""", [pedido_id])
    return p


# ---------- rotas ----------
@router.get("")
def listar(tipo: Optional[str] = None, status: Optional[str] = None, oficina_id: Optional[int] = None,
           q: str = Query(default="", max_length=60), de: Optional[str] = None, ate: Optional[str] = None,
           limite: int = Query(default=100, le=500), user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    sql = """SELECT P.ID, P.TIPO, P.STATUS, P.NUMERO_ORCAMENTO, P.NUMERO_PEDIDO, P.ABERTO_EM, P.PREVISAO_ENTREGA,
                    P.TOTAL_CENT, P.GUINCHO, C.NOME CLIENTE_NOME, V.PLACA, V.MARCA, V.MODELO, F.NOME FUNCIONARIO_NOME
             FROM PEDIDO P JOIN CLIENTE C ON C.ID = P.CLIENTE_ID JOIN VEICULO V ON V.ID = P.VEICULO_ID
             LEFT JOIN FUNCIONARIO F ON F.ID = P.FUNCIONARIO_ID WHERE P.EMPRESA_ID = %s"""
    params = [user["empresa_id"]]
    of = user.get("oficina_id") or oficina_id
    if of:
        sql += " AND P.OFICINA_ID = %s"; params.append(of)
    if tipo:
        sql += " AND P.TIPO = %s"; params.append(tipo)
    if status:
        sql += " AND P.STATUS = %s"; params.append(status)
    if de:
        sql += " AND P.ABERTO_EM >= %s"; params.append(f"{de} 00:00:00")
    if ate:
        sql += " AND P.ABERTO_EM <= %s"; params.append(f"{ate} 23:59:59")
    t = q.strip()
    if t:
        sql += " AND (C.NOME LIKE %s OR V.PLACA LIKE %s OR P.NUMERO_PEDIDO = %s OR P.NUMERO_ORCAMENTO = %s)"
        params += [f"%{t}%", f"{t.replace('-', '').upper()}%", t if t.isdigit() else 0, t if t.isdigit() else 0]
    sql += " ORDER BY P.ABERTO_EM DESC LIMIT %s"
    params.append(limite)
    return db.todos(con, sql, params)


@router.get("/{pedido_id}")
def obter(pedido_id: int, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    _carregar(con, pedido_id, user)
    return _detalhe(con, pedido_id)


@router.post("")
def criar(d: PedidoIn, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    if user.get("oficina_id") and user["oficina_id"] != d.oficina_id:
        raise HTTPException(status_code=403, detail="Oficina fora do seu acesso")
    v = db.um(con, "SELECT ID FROM VEICULO WHERE ID = %s AND CLIENTE_ID = %s AND EMPRESA_ID = %s",
              [d.veiculo_id, d.cliente_id, user["empresa_id"]])
    if not v:
        raise HTTPException(status_code=400, detail="Veículo não pertence a este cliente")
    num_orc = _proximo_numero(con, user["empresa_id"], "ORCAMENTO")
    num_ped = _proximo_numero(con, user["empresa_id"], "PEDIDO") if d.tipo == "PEDIDO" else None
    status = "APROVADO" if d.tipo == "PEDIDO" else "ABERTO"
    novo = db.executar(con, """INSERT INTO PEDIDO (EMPRESA_ID, OFICINA_ID, NUMERO_ORCAMENTO, NUMERO_PEDIDO, TIPO, STATUS, CLIENTE_ID,
                               VEICULO_ID, AGENDA_ID, FUNCIONARIO_ID, KM_ENTRADA, GUINCHO, QUEIXA, DIAGNOSTICO, OBSERVACAO,
                               PREVISAO_ENTREGA, VALIDADE_ORCAMENTO, DESCONTO_CENT, APROVADO_EM, CRIADO_POR)
                               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                      [user["empresa_id"], d.oficina_id, num_orc, num_ped, d.tipo, status, d.cliente_id, d.veiculo_id,
                       d.agenda_id, d.funcionario_id, d.km_entrada, int(d.guincho), d.queixa, d.diagnostico, d.observacao,
                       d.previsao_entrega, d.validade_orcamento, d.desconto_cent,
                       datetime.now() if d.tipo == "PEDIDO" else None, int(user["sub"])])
    if d.km_entrada:
        db.executar(con, "UPDATE VEICULO SET KM_ATUAL = %s WHERE ID = %s AND (KM_ATUAL IS NULL OR KM_ATUAL < %s)",
                    [d.km_entrada, d.veiculo_id, d.km_entrada])
    if d.agenda_id:
        db.executar(con, "UPDATE AGENDA SET STATUS = 'EM_ATENDIMENTO' WHERE ID = %s AND STATUS IN ('AGENDADO','CONFIRMADO','CHEGOU')",
                    [d.agenda_id])
    return {"id": novo, "numero_orcamento": num_orc, "numero_pedido": num_ped}


@router.put("/{pedido_id}")
def editar_cabecalho(pedido_id: int, d: PedidoIn, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    p = _carregar(con, pedido_id, user)
    _exigir_editavel(p)
    db.executar(con, """UPDATE PEDIDO SET FUNCIONARIO_ID=%s, KM_ENTRADA=%s, GUINCHO=%s, QUEIXA=%s, DIAGNOSTICO=%s, OBSERVACAO=%s,
                        PREVISAO_ENTREGA=%s, VALIDADE_ORCAMENTO=%s, DESCONTO_CENT=%s WHERE ID=%s""",
                [d.funcionario_id, d.km_entrada, int(d.guincho), d.queixa, d.diagnostico, d.observacao, d.previsao_entrega,
                 d.validade_orcamento, d.desconto_cent, pedido_id])
    _recalcular(con, pedido_id)
    return {"ok": True}


# ----- itens de serviço -----
@router.post("/{pedido_id}/servicos")
def add_servico(pedido_id: int, d: ServicoItemIn, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    p = _carregar(con, pedido_id, user)
    _exigir_editavel(p)
    descricao, tempo, vhora, vcent = d.descricao, 60, d.valor_hora_cent or 0, d.valor_cent
    if d.servico_id:
        s = db.um(con, "SELECT * FROM SERVICO WHERE ID = %s AND EMPRESA_ID = %s", [d.servico_id, user["empresa_id"]])
        if not s:
            raise HTTPException(status_code=404, detail="Serviço não encontrado")
        descricao = descricao or s["NOME"]
        tempo = s["TEMPO_PREVISTO_MIN"]
        vhora = d.valor_hora_cent if d.valor_hora_cent is not None else s["VALOR_HORA_CENT"]
        if vcent is None:
            vcent = valor_previsto_cent(vhora, tempo, s["VALOR_FIXO_CENT"]) if d.horas is None else round(vhora * d.horas)
    if not descricao:
        raise HTTPException(status_code=400, detail="Informe o serviço ou uma descrição")
    horas = d.horas if d.horas is not None else round(tempo / 60, 2)
    if vcent is None:
        vcent = round(vhora * horas)
    novo = db.executar(con, """INSERT INTO PEDIDO_SERVICO (PEDIDO_ID, SERVICO_ID, DESCRICAO, FUNCIONARIO_ID, TEMPO_PREVISTO_MIN, HORAS,
                               VALOR_HORA_CENT, VALOR_CENT, AUTORIZADO) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                      [pedido_id, d.servico_id, descricao.strip(), d.funcionario_id or p["FUNCIONARIO_ID"], tempo, horas,
                       vhora, int(vcent), int(d.autorizado)])
    _recalcular(con, pedido_id)
    return {"id": novo, "valor_cent": int(vcent)}


@router.put("/{pedido_id}/servicos/{item_id}")
def edit_servico(pedido_id: int, item_id: int, d: ServicoItemIn, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    p = _carregar(con, pedido_id, user)
    _exigir_editavel(p)
    it = db.um(con, "SELECT * FROM PEDIDO_SERVICO WHERE ID = %s AND PEDIDO_ID = %s", [item_id, pedido_id])
    if not it:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    horas = d.horas if d.horas is not None else float(it["HORAS"])
    vhora = d.valor_hora_cent if d.valor_hora_cent is not None else it["VALOR_HORA_CENT"]
    vcent = d.valor_cent if d.valor_cent is not None else round(vhora * horas)
    db.executar(con, """UPDATE PEDIDO_SERVICO SET DESCRICAO=%s, FUNCIONARIO_ID=%s, HORAS=%s, VALOR_HORA_CENT=%s, VALOR_CENT=%s,
                        AUTORIZADO=%s WHERE ID=%s""",
                [(d.descricao or it["DESCRICAO"]).strip(), d.funcionario_id if d.funcionario_id is not None else it["FUNCIONARIO_ID"],
                 horas, vhora, int(vcent), int(d.autorizado), item_id])
    _recalcular(con, pedido_id)
    return {"ok": True}


@router.delete("/{pedido_id}/servicos/{item_id}")
def del_servico(pedido_id: int, item_id: int, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    p = _carregar(con, pedido_id, user)
    _exigir_editavel(p)
    db.executar(con, "DELETE FROM PEDIDO_SERVICO WHERE ID = %s AND PEDIDO_ID = %s", [item_id, pedido_id])
    _recalcular(con, pedido_id)
    return {"ok": True}


@router.patch("/{pedido_id}/servicos/{item_id}/execucao")
def exec_servico(pedido_id: int, item_id: int, d: ExecucaoIn, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    """Mecânico registra o que foi executado (texto do tablet/áudio transcrito)."""
    p = _carregar(con, pedido_id, user)
    if p["TIPO"] != "PEDIDO":
        raise HTTPException(status_code=409, detail="Só pedido aprovado tem execução")
    n = db.executar(con, """UPDATE PEDIDO_SERVICO SET EXECUTADO=%s, DESCRICAO_EXECUTADO=%s,
                            FUNCIONARIO_ID=COALESCE(%s, FUNCIONARIO_ID),
                            INICIADO_EM=COALESCE(INICIADO_EM, NOW()), CONCLUIDO_EM=IF(%s, NOW(), NULL)
                            WHERE ID=%s AND PEDIDO_ID=%s""",
                    [int(d.executado), d.descricao_executado, d.funcionario_id, int(d.executado), item_id, pedido_id])
    if not n:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    if p["STATUS"] == "APROVADO":
        db.executar(con, "UPDATE PEDIDO SET STATUS = 'EM_EXECUCAO' WHERE ID = %s", [pedido_id])
    return {"ok": True}


# ----- itens de peça -----
@router.post("/{pedido_id}/pecas")
def add_peca(pedido_id: int, d: PecaItemIn, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    p = _carregar(con, pedido_id, user)
    _exigir_editavel(p)
    descricao, vunit = d.descricao, d.valor_unit_cent
    if d.peca_id:
        pe = db.um(con, "SELECT * FROM PECA WHERE ID = %s AND EMPRESA_ID = %s", [d.peca_id, user["empresa_id"]])
        if not pe:
            raise HTTPException(status_code=404, detail="Peça não encontrada")
        descricao = descricao or pe["NOME"]
        vunit = vunit if vunit is not None else pe["PRECO_VENDA_CENT"]
    if not descricao:
        raise HTTPException(status_code=400, detail="Informe a peça ou uma descrição")
    vunit = vunit or 0
    vcent = round(vunit * d.quantidade)
    novo = db.executar(con, """INSERT INTO PEDIDO_PECA (PEDIDO_ID, PECA_ID, DESCRICAO, QUANTIDADE, VALOR_UNIT_CENT, VALOR_CENT, AUTORIZADO)
                               VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                      [pedido_id, d.peca_id, descricao.strip(), d.quantidade, vunit, vcent, int(d.autorizado)])
    _recalcular(con, pedido_id)
    return {"id": novo, "valor_cent": vcent}


@router.put("/{pedido_id}/pecas/{item_id}")
def edit_peca(pedido_id: int, item_id: int, d: PecaItemIn, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    p = _carregar(con, pedido_id, user)
    _exigir_editavel(p)
    it = db.um(con, "SELECT * FROM PEDIDO_PECA WHERE ID = %s AND PEDIDO_ID = %s", [item_id, pedido_id])
    if not it:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    vunit = d.valor_unit_cent if d.valor_unit_cent is not None else it["VALOR_UNIT_CENT"]
    db.executar(con, "UPDATE PEDIDO_PECA SET DESCRICAO=%s, QUANTIDADE=%s, VALOR_UNIT_CENT=%s, VALOR_CENT=%s, AUTORIZADO=%s WHERE ID=%s",
                [(d.descricao or it["DESCRICAO"]).strip(), d.quantidade, vunit, round(vunit * d.quantidade), int(d.autorizado), item_id])
    _recalcular(con, pedido_id)
    return {"ok": True}


@router.delete("/{pedido_id}/pecas/{item_id}")
def del_peca(pedido_id: int, item_id: int, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    p = _carregar(con, pedido_id, user)
    _exigir_editavel(p)
    db.executar(con, "DELETE FROM PEDIDO_PECA WHERE ID = %s AND PEDIDO_ID = %s", [item_id, pedido_id])
    _recalcular(con, pedido_id)
    return {"ok": True}


# ----- transições -----
@router.post("/{pedido_id}/aprovar", dependencies=[Depends(requer_nivel(2))])
def aprovar(pedido_id: int, d: AprovacaoIn, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    """Orçamento aprovado pelo cliente vira PEDIDO (recebe NUMERO_PEDIDO)."""
    p = _carregar(con, pedido_id, user)
    if p["TIPO"] != "ORCAMENTO" or p["STATUS"] in ("RECUSADO", "CANCELADO"):
        raise HTTPException(status_code=409, detail="Este registro não é um orçamento aberto")
    if not db.um(con, "SELECT 1 FROM PEDIDO_SERVICO WHERE PEDIDO_ID = %s AND AUTORIZADO = 1 "
                      "UNION SELECT 1 FROM PEDIDO_PECA WHERE PEDIDO_ID = %s AND AUTORIZADO = 1 LIMIT 1", [pedido_id, pedido_id]):
        raise HTTPException(status_code=400, detail="Orçamento sem itens autorizados")
    num = _proximo_numero(con, user["empresa_id"], "PEDIDO")
    db.executar(con, """UPDATE PEDIDO SET TIPO='PEDIDO', STATUS='APROVADO', NUMERO_PEDIDO=%s, APROVADO_EM=NOW(), APROVADO_POR_NOME=%s,
                        FUNCIONARIO_ID=COALESCE(%s, FUNCIONARIO_ID), PREVISAO_ENTREGA=COALESCE(%s, PREVISAO_ENTREGA) WHERE ID=%s""",
                [num, d.aprovado_por_nome.strip(), d.funcionario_id, d.previsao_entrega, pedido_id])
    return {"ok": True, "numero_pedido": num}


@router.post("/{pedido_id}/status", dependencies=[Depends(requer_nivel(2))])
def mudar_status(pedido_id: int, status: str = Query(pattern="^(ENVIADO|RECUSADO|EM_EXECUCAO|AGUARDANDO_PECA|CONCLUIDO|ENTREGUE|CANCELADO)$"),
                 user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    p = _carregar(con, pedido_id, user)
    if p["STATUS"] in ("FATURADO", "CANCELADO"):
        raise HTTPException(status_code=409, detail=f"Pedido {p['STATUS']} não muda mais de status")
    if status in ("ENVIADO", "RECUSADO") and p["TIPO"] != "ORCAMENTO":
        raise HTTPException(status_code=409, detail="Status de orçamento em um pedido")
    if status in ("EM_EXECUCAO", "AGUARDANDO_PECA", "CONCLUIDO", "ENTREGUE") and p["TIPO"] != "PEDIDO":
        raise HTTPException(status_code=409, detail="Aprove o orçamento antes")
    if status == "CONCLUIDO":
        pend = db.um(con, "SELECT COUNT(*) N FROM PEDIDO_SERVICO WHERE PEDIDO_ID = %s AND AUTORIZADO = 1 AND EXECUTADO = 0", [pedido_id])
        if pend["N"]:
            raise HTTPException(status_code=409, detail=f"{pend['N']} serviço(s) autorizado(s) ainda não executado(s)")
    campos = {"CONCLUIDO": ", CONCLUIDO_EM=NOW()", "ENTREGUE": ", ENTREGUE_EM=NOW()"}.get(status, "")
    db.executar(con, f"UPDATE PEDIDO SET STATUS=%s{campos} WHERE ID=%s", [status, pedido_id])
    if status in ("ENTREGUE", "CANCELADO") and p["AGENDA_ID"]:
        db.executar(con, "UPDATE AGENDA SET STATUS = %s WHERE ID = %s",
                    ["CONCLUIDO" if status == "ENTREGUE" else "CANCELADO", p["AGENDA_ID"]])
    return {"ok": True}
