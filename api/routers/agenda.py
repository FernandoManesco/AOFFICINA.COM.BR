"""Agenda por oficina, com recursos (funcionário e/ou equipamento).

Regra: um funcionário ou um equipamento não pode ter dois compromissos
sobrepostos (exceto CANCELADO/FALTOU). A oficina em si pode ter N ao mesmo tempo.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

import db
from utils.auth import requer_nivel, usuario_atual

router = APIRouter(prefix="/agenda", tags=["agenda"], dependencies=[Depends(requer_nivel(3))])

STATUS_LIVRES = ("CANCELADO", "FALTOU")


class AgendaIn(BaseModel):
    oficina_id: int
    inicio: datetime
    fim: datetime
    tipo: str = "SERVICO"
    status: str = "AGENDADO"
    cliente_id: Optional[int] = None
    veiculo_id: Optional[int] = None
    funcionario_id: Optional[int] = None
    equipamento_id: Optional[int] = None
    titulo: str = Field(min_length=2, max_length=120)
    descricao: Optional[str] = None
    guincho: bool = False


def _oficina_permitida(user: dict, oficina_id: int):
    if user.get("oficina_id") and user["oficina_id"] != oficina_id:
        raise HTTPException(status_code=403, detail="Oficina fora do seu acesso")


def _conflito(con, campo: str, recurso_id: int, inicio, fim, ignorar_id: Optional[int]):
    sql = f"""SELECT ID, TITULO, INICIO, FIM FROM AGENDA WHERE {campo} = %s AND STATUS NOT IN %s
              AND INICIO < %s AND FIM > %s"""
    params = [recurso_id, STATUS_LIVRES, fim, inicio]
    if ignorar_id:
        sql += " AND ID <> %s"
        params.append(ignorar_id)
    return db.um(con, sql + " LIMIT 1", params)


def _validar(con, d: AgendaIn, user: dict, ignorar_id: Optional[int] = None):
    _oficina_permitida(user, d.oficina_id)
    if d.fim <= d.inicio:
        raise HTTPException(status_code=400, detail="Fim deve ser depois do início")
    if not db.um(con, "SELECT ID FROM OFICINA WHERE ID = %s AND EMPRESA_ID = %s", [d.oficina_id, user["empresa_id"]]):
        raise HTTPException(status_code=404, detail="Oficina não encontrada")
    if d.funcionario_id:
        c = _conflito(con, "FUNCIONARIO_ID", d.funcionario_id, d.inicio, d.fim, ignorar_id)
        if c:
            raise HTTPException(status_code=409, detail=f"Funcionário já ocupado: {c['TITULO']} ({c['INICIO']:%d/%m %H:%M})")
    if d.equipamento_id:
        c = _conflito(con, "EQUIPAMENTO_ID", d.equipamento_id, d.inicio, d.fim, ignorar_id)
        if c:
            raise HTTPException(status_code=409, detail=f"Equipamento já ocupado: {c['TITULO']} ({c['INICIO']:%d/%m %H:%M})")


@router.get("")
def listar(oficina_id: int, de: datetime, ate: datetime,
           funcionario_id: Optional[int] = None, equipamento_id: Optional[int] = None,
           user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    _oficina_permitida(user, oficina_id)
    sql = """SELECT A.*, C.NOME CLIENTE_NOME, V.PLACA, V.MARCA, V.MODELO,
                    F.NOME FUNCIONARIO_NOME, F.COR_AGENDA COR_FUNC, Q.NOME EQUIPAMENTO_NOME, Q.COR_AGENDA COR_EQUIP
             FROM AGENDA A
             LEFT JOIN CLIENTE C ON C.ID = A.CLIENTE_ID
             LEFT JOIN VEICULO V ON V.ID = A.VEICULO_ID
             LEFT JOIN FUNCIONARIO F ON F.ID = A.FUNCIONARIO_ID
             LEFT JOIN EQUIPAMENTO Q ON Q.ID = A.EQUIPAMENTO_ID
             WHERE A.OFICINA_ID = %s AND A.INICIO < %s AND A.FIM > %s"""
    params = [oficina_id, ate, de]
    if funcionario_id:
        sql += " AND A.FUNCIONARIO_ID = %s"
        params.append(funcionario_id)
    if equipamento_id:
        sql += " AND A.EQUIPAMENTO_ID = %s"
        params.append(equipamento_id)
    return db.todos(con, sql + " ORDER BY A.INICIO", params)


@router.get("/disponibilidade")
def disponibilidade(oficina_id: int, dia: str = Query(pattern=r"^\d{4}-\d{2}-\d{2}$"),
                    user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    """Para a recepção: ocupação de cada funcionário e equipamento no dia."""
    _oficina_permitida(user, oficina_id)
    de, ate = f"{dia} 00:00:00", f"{dia} 23:59:59"
    funcs = db.todos(con, """SELECT ID, NOME, COR_AGENDA FROM FUNCIONARIO
                             WHERE EMPRESA_ID = %s AND ATIVO = 1 AND (OFICINA_ID = %s OR OFICINA_ID IS NULL) ORDER BY NOME""",
                     [user["empresa_id"], oficina_id])
    equips = db.todos(con, "SELECT ID, NOME, TIPO, COR_AGENDA FROM EQUIPAMENTO WHERE OFICINA_ID = %s AND ATIVO = 1 ORDER BY TIPO, NOME",
                      [oficina_id])
    ocup = db.todos(con, """SELECT ID, FUNCIONARIO_ID, EQUIPAMENTO_ID, INICIO, FIM, TITULO, STATUS FROM AGENDA
                            WHERE OFICINA_ID = %s AND STATUS NOT IN %s AND INICIO <= %s AND FIM >= %s ORDER BY INICIO""",
                    [oficina_id, STATUS_LIVRES, ate, de])
    for f in funcs:
        f["ocupacoes"] = [o for o in ocup if o["FUNCIONARIO_ID"] == f["ID"]]
    for e in equips:
        e["ocupacoes"] = [o for o in ocup if o["EQUIPAMENTO_ID"] == e["ID"]]
    return {"dia": dia, "funcionarios": funcs, "equipamentos": equips}


@router.post("")
def criar(d: AgendaIn, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    _validar(con, d, user)
    novo = db.executar(con, """INSERT INTO AGENDA (OFICINA_ID, INICIO, FIM, TIPO, STATUS, CLIENTE_ID, VEICULO_ID, FUNCIONARIO_ID,
                               EQUIPAMENTO_ID, TITULO, DESCRICAO, GUINCHO, CRIADO_POR)
                               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                      [d.oficina_id, d.inicio, d.fim, d.tipo, d.status, d.cliente_id, d.veiculo_id, d.funcionario_id,
                       d.equipamento_id, d.titulo.strip(), d.descricao, int(d.guincho), int(user["sub"])])
    return {"id": novo}


@router.put("/{agenda_id}")
def editar(agenda_id: int, d: AgendaIn, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    _validar(con, d, user, ignorar_id=agenda_id)
    n = db.executar(con, """UPDATE AGENDA SET OFICINA_ID=%s, INICIO=%s, FIM=%s, TIPO=%s, STATUS=%s, CLIENTE_ID=%s, VEICULO_ID=%s,
                            FUNCIONARIO_ID=%s, EQUIPAMENTO_ID=%s, TITULO=%s, DESCRICAO=%s, GUINCHO=%s WHERE ID=%s""",
                    [d.oficina_id, d.inicio, d.fim, d.tipo, d.status, d.cliente_id, d.veiculo_id, d.funcionario_id,
                     d.equipamento_id, d.titulo.strip(), d.descricao, int(d.guincho), agenda_id])
    if not n:
        raise HTTPException(status_code=404, detail="Compromisso não encontrado")
    return {"ok": True}


@router.patch("/{agenda_id}/status")
def mudar_status(agenda_id: int, status: str = Query(pattern="^(AGENDADO|CONFIRMADO|CHEGOU|EM_ATENDIMENTO|CONCLUIDO|FALTOU|CANCELADO)$"),
                 user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    a = db.um(con, "SELECT OFICINA_ID FROM AGENDA WHERE ID = %s", [agenda_id])
    if not a:
        raise HTTPException(status_code=404, detail="Compromisso não encontrado")
    _oficina_permitida(user, a["OFICINA_ID"])
    db.executar(con, "UPDATE AGENDA SET STATUS = %s WHERE ID = %s", [status, agenda_id])
    return {"ok": True}
