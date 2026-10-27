"""Cadastro de mão de obra: valor/hora, tempo previsto e, opcionalmente, valor fixo."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

import db
from utils.auth import requer_nivel, usuario_atual

router = APIRouter(prefix="/servicos", tags=["servicos"], dependencies=[Depends(requer_nivel(3))])


class ServicoIn(BaseModel):
    codigo: str = Field(min_length=1, max_length=20)
    nome: str = Field(min_length=2, max_length=120)
    descricao: Optional[str] = None
    categoria: Optional[str] = Field(default=None, max_length=40)
    valor_hora_cent: int = Field(default=0, ge=0)
    tempo_previsto_min: int = Field(default=60, ge=1)
    valor_fixo_cent: Optional[int] = Field(default=None, ge=0)
    ativo: bool = True


def valor_previsto_cent(valor_hora_cent: int, tempo_min: int, valor_fixo_cent: Optional[int]) -> int:
    """Regra de preço: fixo se houver; senão valor_hora × tempo (arredondado ao centavo)."""
    if valor_fixo_cent is not None:
        return int(valor_fixo_cent)
    return round(valor_hora_cent * tempo_min / 60)


@router.get("")
def buscar(q: str = Query(default="", max_length=60), ativos: bool = True,
           limite: int = Query(default=100, le=500), user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    sql = "SELECT * FROM SERVICO WHERE EMPRESA_ID = %s"
    params = [user["empresa_id"]]
    if ativos:
        sql += " AND ATIVO = 1"
    t = q.strip()
    if t:
        sql += " AND (CODIGO LIKE %s OR NOME LIKE %s OR CATEGORIA LIKE %s)"
        params += [f"{t}%", f"%{t}%", f"%{t}%"]
    sql += " ORDER BY CATEGORIA, NOME LIMIT %s"
    params.append(limite)
    rows = db.todos(con, sql, params)
    for r in rows:
        r["VALOR_PREVISTO_CENT"] = valor_previsto_cent(r["VALOR_HORA_CENT"], r["TEMPO_PREVISTO_MIN"], r["VALOR_FIXO_CENT"])
    return rows


@router.post("", dependencies=[Depends(requer_nivel(1))])
def criar(d: ServicoIn, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    cod = d.codigo.strip().upper()
    if db.um(con, "SELECT ID FROM SERVICO WHERE EMPRESA_ID = %s AND CODIGO = %s", [user["empresa_id"], cod]):
        raise HTTPException(status_code=409, detail="Já existe serviço com este código")
    novo = db.executar(con, """INSERT INTO SERVICO (EMPRESA_ID, CODIGO, NOME, DESCRICAO, CATEGORIA, VALOR_HORA_CENT,
                               TEMPO_PREVISTO_MIN, VALOR_FIXO_CENT, ATIVO) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                      [user["empresa_id"], cod, d.nome.strip(), d.descricao, d.categoria, d.valor_hora_cent,
                       d.tempo_previsto_min, d.valor_fixo_cent, int(d.ativo)])
    return {"id": novo}


@router.put("/{servico_id}", dependencies=[Depends(requer_nivel(1))])
def editar(servico_id: int, d: ServicoIn, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    cod = d.codigo.strip().upper()
    if db.um(con, "SELECT ID FROM SERVICO WHERE EMPRESA_ID = %s AND CODIGO = %s AND ID <> %s", [user["empresa_id"], cod, servico_id]):
        raise HTTPException(status_code=409, detail="Outro serviço já usa este código")
    n = db.executar(con, """UPDATE SERVICO SET CODIGO=%s, NOME=%s, DESCRICAO=%s, CATEGORIA=%s, VALOR_HORA_CENT=%s,
                            TEMPO_PREVISTO_MIN=%s, VALOR_FIXO_CENT=%s, ATIVO=%s WHERE ID=%s AND EMPRESA_ID=%s""",
                    [cod, d.nome.strip(), d.descricao, d.categoria, d.valor_hora_cent, d.tempo_previsto_min,
                     d.valor_fixo_cent, int(d.ativo), servico_id, user["empresa_id"]])
    if not n:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    return {"ok": True}
