"""Catálogo de marcas/modelos/anos (importado da FIPE, só leitura pela API).
Usado nos combos da recepção. Todo usuário logado pode consultar."""
from fastapi import APIRouter, Depends, Query

import db

router = APIRouter(prefix="/catalogo", tags=["catalogo"])


@router.get("/marcas")
def marcas(tipo: int = 1, con=Depends(db.get_db_dep)):
    return db.todos(con, """SELECT M.ID, M.NOME, M.CODIGO_FIPE, COUNT(D.ID) QTD_MODELOS
                            FROM CAT_MARCA M LEFT JOIN CAT_MODELO D ON D.MARCA_ID = M.ID
                            WHERE M.TIPO = %s GROUP BY M.ID, M.NOME, M.CODIGO_FIPE
                            HAVING QTD_MODELOS > 0 ORDER BY M.NOME""", [tipo])


@router.get("/marcas/{marca_id}/modelos")
def modelos(marca_id: int, q: str = Query(default="", max_length=40), con=Depends(db.get_db_dep)):
    sql = "SELECT ID, NOME, CODIGO_FIPE FROM CAT_MODELO WHERE MARCA_ID = %s"
    params = [marca_id]
    if q.strip():
        sql += " AND NOME LIKE %s"
        params.append(f"%{q.strip()}%")
    return db.todos(con, sql + " ORDER BY NOME LIMIT 500", params)


@router.get("/modelos/{modelo_id}/anos")
def anos(modelo_id: int, con=Depends(db.get_db_dep)):
    return db.todos(con, "SELECT ID, ANO, COMBUSTIVEL, CODIGO_FIPE FROM CAT_ANO WHERE MODELO_ID = %s ORDER BY ANO DESC", [modelo_id])


@router.get("/buscar")
def buscar(q: str = Query(min_length=2, max_length=60), tipo: int = 1, con=Depends(db.get_db_dep)):
    """Busca livre 'marca modelo' para autocomplete na recepção."""
    partes = [p for p in q.strip().split() if p]
    sql = """SELECT D.ID MODELO_ID, M.ID MARCA_ID, M.NOME MARCA, D.NOME MODELO, D.CODIGO_FIPE
             FROM CAT_MODELO D JOIN CAT_MARCA M ON M.ID = D.MARCA_ID WHERE M.TIPO = %s"""
    params = [tipo]
    for p in partes[:4]:
        sql += " AND CONCAT(M.NOME, ' ', D.NOME) LIKE %s"
        params.append(f"%{p}%")
    return db.todos(con, sql + " ORDER BY M.NOME, D.NOME LIMIT 30", params)
