"""Cadastro de peças (sem estoque por lote ainda — v003)."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

import db
from utils.auth import requer_nivel, usuario_atual

router = APIRouter(prefix="/pecas", tags=["pecas"], dependencies=[Depends(requer_nivel(3))])


class PecaIn(BaseModel):
    codigo: str = Field(min_length=1, max_length=30)
    codigo_fabricante: Optional[str] = Field(default=None, max_length=40)
    codigo_barras: Optional[str] = Field(default=None, max_length=20)
    nome: str = Field(min_length=2, max_length=120)
    descricao: Optional[str] = None
    fabricante: Optional[str] = Field(default=None, max_length=60)
    aplicacao: Optional[str] = Field(default=None, max_length=255)
    unidade: str = Field(default="UN", max_length=6)
    ncm: Optional[str] = Field(default=None, max_length=8)
    preco_custo_cent: int = Field(default=0, ge=0)
    preco_venda_cent: int = Field(default=0, ge=0)
    estoque_min: float = Field(default=0, ge=0)
    tem_validade: bool = False
    ativo: bool = True


@router.get("")
def buscar(q: str = Query(default="", max_length=60), ativos: bool = True,
           limite: int = Query(default=50, le=500), user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    sql = "SELECT * FROM PECA WHERE EMPRESA_ID = %s"
    params = [user["empresa_id"]]
    if ativos:
        sql += " AND ATIVO = 1"
    t = q.strip()
    if t:
        sql += " AND (CODIGO LIKE %s OR CODIGO_FABRICANTE LIKE %s OR CODIGO_BARRAS = %s OR NOME LIKE %s OR APLICACAO LIKE %s)"
        params += [f"{t}%", f"{t}%", t, f"%{t}%", f"%{t}%"]
    sql += " ORDER BY NOME LIMIT %s"
    params.append(limite)
    return db.todos(con, sql, params)


@router.get("/{peca_id}")
def obter(peca_id: int, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    p = db.um(con, "SELECT * FROM PECA WHERE ID = %s AND EMPRESA_ID = %s", [peca_id, user["empresa_id"]])
    if not p:
        raise HTTPException(status_code=404, detail="Peça não encontrada")
    return p


@router.post("", dependencies=[Depends(requer_nivel(2))])
def criar(d: PecaIn, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    cod = d.codigo.strip().upper()
    if db.um(con, "SELECT ID FROM PECA WHERE EMPRESA_ID = %s AND CODIGO = %s", [user["empresa_id"], cod]):
        raise HTTPException(status_code=409, detail="Já existe peça com este código")
    novo = db.executar(con, """INSERT INTO PECA (EMPRESA_ID, CODIGO, CODIGO_FABRICANTE, CODIGO_BARRAS, NOME, DESCRICAO, FABRICANTE,
                               APLICACAO, UNIDADE, NCM, PRECO_CUSTO_CENT, PRECO_VENDA_CENT, ESTOQUE_MIN, TEM_VALIDADE, ATIVO)
                               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                      [user["empresa_id"], cod, d.codigo_fabricante, d.codigo_barras, d.nome.strip(), d.descricao, d.fabricante,
                       d.aplicacao, d.unidade.upper(), d.ncm, d.preco_custo_cent, d.preco_venda_cent, d.estoque_min,
                       int(d.tem_validade), int(d.ativo)])
    return {"id": novo}


@router.put("/{peca_id}", dependencies=[Depends(requer_nivel(2))])
def editar(peca_id: int, d: PecaIn, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    cod = d.codigo.strip().upper()
    if db.um(con, "SELECT ID FROM PECA WHERE EMPRESA_ID = %s AND CODIGO = %s AND ID <> %s", [user["empresa_id"], cod, peca_id]):
        raise HTTPException(status_code=409, detail="Outra peça já usa este código")
    n = db.executar(con, """UPDATE PECA SET CODIGO=%s, CODIGO_FABRICANTE=%s, CODIGO_BARRAS=%s, NOME=%s, DESCRICAO=%s, FABRICANTE=%s,
                            APLICACAO=%s, UNIDADE=%s, NCM=%s, PRECO_CUSTO_CENT=%s, PRECO_VENDA_CENT=%s, ESTOQUE_MIN=%s,
                            TEM_VALIDADE=%s, ATIVO=%s WHERE ID=%s AND EMPRESA_ID=%s""",
                    [cod, d.codigo_fabricante, d.codigo_barras, d.nome.strip(), d.descricao, d.fabricante, d.aplicacao,
                     d.unidade.upper(), d.ncm, d.preco_custo_cent, d.preco_venda_cent, d.estoque_min, int(d.tem_validade),
                     int(d.ativo), peca_id, user["empresa_id"]])
    if not n:
        raise HTTPException(status_code=404, detail="Peça não encontrada")
    return {"ok": True}
