"""Clientes — busca por nome/CPF-CNPJ/placa, CRUD. Remoção = inativação (histórico fica)."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

import db
from utils.auth import requer_nivel, usuario_atual

router = APIRouter(prefix="/clientes", tags=["clientes"], dependencies=[Depends(requer_nivel(2))])


class ClienteIn(BaseModel):
    tipo_pessoa: str = Field(default="F", pattern="^[FJ]$")
    nome: str = Field(min_length=2, max_length=120)
    cpf_cnpj: Optional[str] = Field(default=None, max_length=18)
    telefone: Optional[str] = None
    whatsapp: Optional[str] = None
    email: Optional[str] = None
    cep: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = Field(default=None, max_length=2)
    observacao: Optional[str] = None
    ativo: bool = True


def _digitos(s):
    if not s:
        return None
    d = "".join(ch for ch in s if ch.isdigit())
    return d or None


@router.get("")
def buscar(q: str = Query(default="", max_length=60), ativos: bool = True,
           limite: int = Query(default=50, le=500), user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    """q pode ser parte do nome, CPF/CNPJ (só dígitos) ou placa (busca pelos veículos)."""
    termo = q.strip()
    dig = _digitos(termo)
    placa = termo.replace("-", "").upper()
    sql = """SELECT DISTINCT C.ID, C.NOME, C.CPF_CNPJ, C.TELEFONE, C.WHATSAPP, C.CIDADE, C.ATIVO,
                    (SELECT COUNT(*) FROM VEICULO V WHERE V.CLIENTE_ID = C.ID AND V.ATIVO = 1) QTD_VEICULOS
             FROM CLIENTE C LEFT JOIN VEICULO V2 ON V2.CLIENTE_ID = C.ID
             WHERE C.EMPRESA_ID = %s"""
    params = [user["empresa_id"]]
    if ativos:
        sql += " AND C.ATIVO = 1"
    if termo:
        sql += " AND (C.NOME LIKE %s OR V2.PLACA LIKE %s"
        params += [f"%{termo}%", f"{placa}%"]
        if dig:
            sql += " OR C.CPF_CNPJ LIKE %s OR C.TELEFONE LIKE %s OR C.WHATSAPP LIKE %s"
            params += [f"{dig}%", f"%{dig}%", f"%{dig}%"]
        sql += ")"
    sql += " ORDER BY C.NOME LIMIT %s"
    params.append(limite)
    return db.todos(con, sql, params)


@router.get("/{cliente_id}")
def obter(cliente_id: int, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    c = db.um(con, "SELECT * FROM CLIENTE WHERE ID = %s AND EMPRESA_ID = %s", [cliente_id, user["empresa_id"]])
    if not c:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    c["veiculos"] = db.todos(con, "SELECT * FROM VEICULO WHERE CLIENTE_ID = %s ORDER BY ATIVO DESC, PLACA", [cliente_id])
    return c


@router.post("")
def criar(d: ClienteIn, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    doc = _digitos(d.cpf_cnpj)
    if doc and len(doc) not in (11, 14):
        raise HTTPException(status_code=400, detail="CPF/CNPJ inválido")
    if doc and db.um(con, "SELECT ID FROM CLIENTE WHERE EMPRESA_ID = %s AND CPF_CNPJ = %s", [user["empresa_id"], doc]):
        raise HTTPException(status_code=409, detail="Já existe cliente com este CPF/CNPJ")
    novo = db.executar(con, """INSERT INTO CLIENTE (EMPRESA_ID, TIPO_PESSOA, NOME, CPF_CNPJ, TELEFONE, WHATSAPP, EMAIL, CEP,
                               LOGRADOURO, NUMERO, COMPLEMENTO, BAIRRO, CIDADE, UF, OBSERVACAO, ATIVO)
                               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                      [user["empresa_id"], d.tipo_pessoa, d.nome.strip(), doc, d.telefone, d.whatsapp, d.email,
                       _digitos(d.cep), d.logradouro, d.numero, d.complemento, d.bairro, d.cidade,
                       (d.uf or "").upper() or None, d.observacao, int(d.ativo)])
    return {"id": novo}


@router.put("/{cliente_id}")
def editar(cliente_id: int, d: ClienteIn, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    doc = _digitos(d.cpf_cnpj)
    if doc and len(doc) not in (11, 14):
        raise HTTPException(status_code=400, detail="CPF/CNPJ inválido")
    if doc and db.um(con, "SELECT ID FROM CLIENTE WHERE EMPRESA_ID = %s AND CPF_CNPJ = %s AND ID <> %s",
                     [user["empresa_id"], doc, cliente_id]):
        raise HTTPException(status_code=409, detail="Outro cliente já usa este CPF/CNPJ")
    n = db.executar(con, """UPDATE CLIENTE SET TIPO_PESSOA=%s, NOME=%s, CPF_CNPJ=%s, TELEFONE=%s, WHATSAPP=%s, EMAIL=%s, CEP=%s,
                            LOGRADOURO=%s, NUMERO=%s, COMPLEMENTO=%s, BAIRRO=%s, CIDADE=%s, UF=%s, OBSERVACAO=%s, ATIVO=%s
                            WHERE ID=%s AND EMPRESA_ID=%s""",
                    [d.tipo_pessoa, d.nome.strip(), doc, d.telefone, d.whatsapp, d.email, _digitos(d.cep), d.logradouro,
                     d.numero, d.complemento, d.bairro, d.cidade, (d.uf or "").upper() or None, d.observacao,
                     int(d.ativo), cliente_id, user["empresa_id"]])
    if not n:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return {"ok": True}


@router.delete("/{cliente_id}", dependencies=[Depends(requer_nivel(1))])
def inativar(cliente_id: int, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    n = db.executar(con, "UPDATE CLIENTE SET ATIVO = 0 WHERE ID = %s AND EMPRESA_ID = %s", [cliente_id, user["empresa_id"]])
    if not n:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return {"ok": True}
