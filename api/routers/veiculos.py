"""Veículos do cliente — placa única por empresa, vínculo opcional com o catálogo."""
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

import db
from utils.auth import requer_nivel, usuario_atual

router = APIRouter(prefix="/veiculos", tags=["veiculos"], dependencies=[Depends(requer_nivel(3))])

RE_PLACA = re.compile(r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$")  # antiga ABC1234 e Mercosul ABC1D23


class VeiculoIn(BaseModel):
    cliente_id: int
    placa: str = Field(min_length=7, max_length=8)
    tipo: int = 1
    marca: str = Field(max_length=60)
    modelo: str = Field(max_length=120)
    ano_fab: Optional[int] = Field(default=None, ge=1950, le=2100)
    ano_modelo: Optional[int] = Field(default=None, ge=1950, le=2100)
    cor: Optional[str] = None
    combustivel: Optional[str] = None
    chassi: Optional[str] = Field(default=None, max_length=17)
    renavam: Optional[str] = Field(default=None, max_length=11)
    km_atual: Optional[int] = Field(default=None, ge=0)
    cat_modelo_id: Optional[int] = None
    codigo_fipe: Optional[str] = None
    observacao: Optional[str] = None
    ativo: bool = True


def normalizar_placa(p: str) -> str:
    p = p.replace("-", "").replace(" ", "").upper()
    if not RE_PLACA.match(p):
        raise HTTPException(status_code=400, detail="Placa inválida (use ABC1234 ou ABC1D23)")
    return p


@router.get("/placa/{placa}")
def por_placa(placa: str, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    """Recepção: digita a placa e já vem cliente + veículo."""
    v = db.um(con, """SELECT V.*, C.NOME CLIENTE_NOME, C.TELEFONE CLIENTE_TELEFONE, C.WHATSAPP CLIENTE_WHATSAPP
                      FROM VEICULO V JOIN CLIENTE C ON C.ID = V.CLIENTE_ID
                      WHERE V.EMPRESA_ID = %s AND V.PLACA = %s""", [user["empresa_id"], normalizar_placa(placa)])
    if not v:
        raise HTTPException(status_code=404, detail="Placa não cadastrada")
    return v


@router.get("")
def listar(cliente_id: Optional[int] = None, q: str = Query(default="", max_length=30),
           limite: int = Query(default=50, le=500), user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    sql = """SELECT V.ID, V.PLACA, V.MARCA, V.MODELO, V.ANO_FAB, V.ANO_MODELO, V.COR, V.KM_ATUAL, V.ATIVO,
                    V.CLIENTE_ID, C.NOME CLIENTE_NOME
             FROM VEICULO V JOIN CLIENTE C ON C.ID = V.CLIENTE_ID WHERE V.EMPRESA_ID = %s"""
    params = [user["empresa_id"]]
    if cliente_id:
        sql += " AND V.CLIENTE_ID = %s"
        params.append(cliente_id)
    if q.strip():
        t = q.strip().replace("-", "").upper()
        sql += " AND (V.PLACA LIKE %s OR V.MODELO LIKE %s OR V.MARCA LIKE %s)"
        params += [f"{t}%", f"%{q.strip()}%", f"%{q.strip()}%"]
    sql += " ORDER BY V.PLACA LIMIT %s"
    params.append(limite)
    return db.todos(con, sql, params)


@router.post("")
def criar(d: VeiculoIn, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    placa = normalizar_placa(d.placa)
    if not db.um(con, "SELECT ID FROM CLIENTE WHERE ID = %s AND EMPRESA_ID = %s", [d.cliente_id, user["empresa_id"]]):
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    if db.um(con, "SELECT ID FROM VEICULO WHERE EMPRESA_ID = %s AND PLACA = %s", [user["empresa_id"], placa]):
        raise HTTPException(status_code=409, detail="Placa já cadastrada")
    novo = db.executar(con, """INSERT INTO VEICULO (EMPRESA_ID, CLIENTE_ID, PLACA, TIPO, MARCA, MODELO, ANO_FAB, ANO_MODELO, COR,
                               COMBUSTIVEL, CHASSI, RENAVAM, KM_ATUAL, CAT_MODELO_ID, CODIGO_FIPE, OBSERVACAO, ATIVO)
                               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                      [user["empresa_id"], d.cliente_id, placa, d.tipo, d.marca.strip(), d.modelo.strip(), d.ano_fab,
                       d.ano_modelo, d.cor, d.combustivel, (d.chassi or "").upper() or None, d.renavam, d.km_atual,
                       d.cat_modelo_id, d.codigo_fipe, d.observacao, int(d.ativo)])
    return {"id": novo, "placa": placa}


@router.put("/{veiculo_id}")
def editar(veiculo_id: int, d: VeiculoIn, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    placa = normalizar_placa(d.placa)
    if db.um(con, "SELECT ID FROM VEICULO WHERE EMPRESA_ID = %s AND PLACA = %s AND ID <> %s",
             [user["empresa_id"], placa, veiculo_id]):
        raise HTTPException(status_code=409, detail="Outro veículo já usa esta placa")
    n = db.executar(con, """UPDATE VEICULO SET CLIENTE_ID=%s, PLACA=%s, TIPO=%s, MARCA=%s, MODELO=%s, ANO_FAB=%s, ANO_MODELO=%s,
                            COR=%s, COMBUSTIVEL=%s, CHASSI=%s, RENAVAM=%s, KM_ATUAL=%s, CAT_MODELO_ID=%s, CODIGO_FIPE=%s,
                            OBSERVACAO=%s, ATIVO=%s WHERE ID=%s AND EMPRESA_ID=%s""",
                    [d.cliente_id, placa, d.tipo, d.marca.strip(), d.modelo.strip(), d.ano_fab, d.ano_modelo, d.cor,
                     d.combustivel, (d.chassi or "").upper() or None, d.renavam, d.km_atual, d.cat_modelo_id,
                     d.codigo_fipe, d.observacao, int(d.ativo), veiculo_id, user["empresa_id"]])
    if not n:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")
    return {"ok": True}


@router.delete("/{veiculo_id}", dependencies=[Depends(requer_nivel(2))])
def inativar(veiculo_id: int, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    n = db.executar(con, "UPDATE VEICULO SET ATIVO = 0 WHERE ID = %s AND EMPRESA_ID = %s", [veiculo_id, user["empresa_id"]])
    if not n:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")
    return {"ok": True}
