"""Empresa (1 por instância), oficinas, funcionários e equipamentos."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

import db
from utils.auth import requer_nivel, usuario_atual

router = APIRouter(prefix="/empresa", tags=["empresa"])


# ---------- Empresa ----------
class EmpresaIn(BaseModel):
    razao_social: str = Field(max_length=120)
    fantasia: str = Field(max_length=80)
    cnpj: Optional[str] = Field(default=None, max_length=14)
    ie: Optional[str] = None
    im: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    cep: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = Field(default=None, max_length=2)


@router.get("")
def get_empresa(user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    e = db.um(con, "SELECT * FROM EMPRESA WHERE ID = %s", [user["empresa_id"]])
    if not e:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    return e


@router.put("", dependencies=[Depends(requer_nivel(0))])
def put_empresa(d: EmpresaIn, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    db.executar(con, """UPDATE EMPRESA SET RAZAO_SOCIAL=%s, FANTASIA=%s, CNPJ=%s, IE=%s, IM=%s, TELEFONE=%s,
                        EMAIL=%s, CEP=%s, LOGRADOURO=%s, NUMERO=%s, COMPLEMENTO=%s, BAIRRO=%s, CIDADE=%s, UF=%s
                        WHERE ID=%s""",
                [d.razao_social, d.fantasia, _digitos(d.cnpj), d.ie, d.im, d.telefone, d.email, _digitos(d.cep),
                 d.logradouro, d.numero, d.complemento, d.bairro, d.cidade, (d.uf or "").upper() or None,
                 user["empresa_id"]])
    return {"ok": True}


# ---------- Oficinas ----------
class OficinaIn(BaseModel):
    nome: str = Field(max_length=80)
    cnpj: Optional[str] = None
    telefone: Optional[str] = None
    whatsapp: Optional[str] = None
    cep: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = Field(default=None, max_length=2)
    hora_abre: str = "08:00"
    hora_fecha: str = "18:00"
    dias_semana: str = "1,2,3,4,5,6"
    ativo: bool = True


def _hora_txt(v) -> str:
    """MySQL TIME chega como timedelta; o front espera 'HH:MM'."""
    if v is None:
        return ""
    seg = int(v.total_seconds()) if hasattr(v, "total_seconds") else int(v)
    return f"{seg // 3600:02d}:{(seg % 3600) // 60:02d}"


@router.get("/oficinas")
def listar_oficinas(user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    sql = "SELECT * FROM OFICINA WHERE EMPRESA_ID = %s"
    params = [user["empresa_id"]]
    if user.get("oficina_id"):
        sql += " AND ID = %s"
        params.append(user["oficina_id"])
    rows = db.todos(con, sql + " ORDER BY NOME", params)
    for r in rows:
        r["HORA_ABRE"] = _hora_txt(r["HORA_ABRE"])
        r["HORA_FECHA"] = _hora_txt(r["HORA_FECHA"])
    return rows


@router.post("/oficinas", dependencies=[Depends(requer_nivel(0))])
def criar_oficina(d: OficinaIn, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    novo = db.executar(con, """INSERT INTO OFICINA (EMPRESA_ID, NOME, CNPJ, TELEFONE, WHATSAPP, CEP, LOGRADOURO, NUMERO,
                               BAIRRO, CIDADE, UF, HORA_ABRE, HORA_FECHA, DIAS_SEMANA, ATIVO)
                               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                      [user["empresa_id"], d.nome, _digitos(d.cnpj), d.telefone, d.whatsapp, _digitos(d.cep),
                       d.logradouro, d.numero, d.bairro, d.cidade, (d.uf or "").upper() or None,
                       d.hora_abre, d.hora_fecha, d.dias_semana, int(d.ativo)])
    return {"id": novo}


@router.put("/oficinas/{oficina_id}", dependencies=[Depends(requer_nivel(0))])
def editar_oficina(oficina_id: int, d: OficinaIn, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    n = db.executar(con, """UPDATE OFICINA SET NOME=%s, CNPJ=%s, TELEFONE=%s, WHATSAPP=%s, CEP=%s, LOGRADOURO=%s,
                            NUMERO=%s, BAIRRO=%s, CIDADE=%s, UF=%s, HORA_ABRE=%s, HORA_FECHA=%s, DIAS_SEMANA=%s, ATIVO=%s
                            WHERE ID=%s AND EMPRESA_ID=%s""",
                    [d.nome, _digitos(d.cnpj), d.telefone, d.whatsapp, _digitos(d.cep), d.logradouro, d.numero,
                     d.bairro, d.cidade, (d.uf or "").upper() or None, d.hora_abre, d.hora_fecha, d.dias_semana,
                     int(d.ativo), oficina_id, user["empresa_id"]])
    return {"ok": True, "alteradas": n}


# ---------- Funcionários ----------
class FuncionarioIn(BaseModel):
    nome: str = Field(max_length=100)
    cpf: Optional[str] = None
    funcao: str = "MECANICO"
    telefone: Optional[str] = None
    oficina_id: Optional[int] = None
    cor_agenda: str = "#0F4C5C"
    ativo: bool = True


@router.get("/funcionarios")
def listar_funcionarios(oficina_id: Optional[int] = None, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    sql = "SELECT F.*, O.NOME OFICINA_NOME FROM FUNCIONARIO F LEFT JOIN OFICINA O ON O.ID = F.OFICINA_ID WHERE F.EMPRESA_ID = %s"
    params = [user["empresa_id"]]
    of = user.get("oficina_id") or oficina_id
    if of:
        sql += " AND (F.OFICINA_ID = %s OR F.OFICINA_ID IS NULL)"
        params.append(of)
    return db.todos(con, sql + " ORDER BY F.ATIVO DESC, F.NOME", params)


@router.post("/funcionarios", dependencies=[Depends(requer_nivel(1))])
def criar_funcionario(d: FuncionarioIn, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    novo = db.executar(con, """INSERT INTO FUNCIONARIO (EMPRESA_ID, OFICINA_ID, NOME, CPF, FUNCAO, TELEFONE, COR_AGENDA, ATIVO)
                               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                      [user["empresa_id"], d.oficina_id, d.nome, _digitos(d.cpf), d.funcao, d.telefone, d.cor_agenda, int(d.ativo)])
    return {"id": novo}


@router.put("/funcionarios/{fid}", dependencies=[Depends(requer_nivel(1))])
def editar_funcionario(fid: int, d: FuncionarioIn, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    n = db.executar(con, """UPDATE FUNCIONARIO SET OFICINA_ID=%s, NOME=%s, CPF=%s, FUNCAO=%s, TELEFONE=%s, COR_AGENDA=%s, ATIVO=%s
                            WHERE ID=%s AND EMPRESA_ID=%s""",
                    [d.oficina_id, d.nome, _digitos(d.cpf), d.funcao, d.telefone, d.cor_agenda, int(d.ativo), fid, user["empresa_id"]])
    return {"ok": True, "alteradas": n}


# ---------- Equipamentos ----------
class EquipamentoIn(BaseModel):
    oficina_id: int
    nome: str = Field(max_length=60)
    tipo: str = "BOX"
    cor_agenda: str = "#B87333"
    ativo: bool = True


@router.get("/equipamentos")
def listar_equipamentos(oficina_id: Optional[int] = None, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    sql = """SELECT Q.*, O.NOME OFICINA_NOME FROM EQUIPAMENTO Q JOIN OFICINA O ON O.ID = Q.OFICINA_ID
             WHERE O.EMPRESA_ID = %s"""
    params = [user["empresa_id"]]
    of = user.get("oficina_id") or oficina_id
    if of:
        sql += " AND Q.OFICINA_ID = %s"
        params.append(of)
    return db.todos(con, sql + " ORDER BY O.NOME, Q.TIPO, Q.NOME", params)


@router.post("/equipamentos", dependencies=[Depends(requer_nivel(1))])
def criar_equipamento(d: EquipamentoIn, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    _checar_oficina(con, d.oficina_id, user)
    novo = db.executar(con, "INSERT INTO EQUIPAMENTO (OFICINA_ID, NOME, TIPO, COR_AGENDA, ATIVO) VALUES (%s,%s,%s,%s,%s)",
                       [d.oficina_id, d.nome, d.tipo, d.cor_agenda, int(d.ativo)])
    return {"id": novo}


@router.put("/equipamentos/{eid}", dependencies=[Depends(requer_nivel(1))])
def editar_equipamento(eid: int, d: EquipamentoIn, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    _checar_oficina(con, d.oficina_id, user)
    n = db.executar(con, "UPDATE EQUIPAMENTO SET OFICINA_ID=%s, NOME=%s, TIPO=%s, COR_AGENDA=%s, ATIVO=%s WHERE ID=%s",
                    [d.oficina_id, d.nome, d.tipo, d.cor_agenda, int(d.ativo), eid])
    return {"ok": True, "alteradas": n}


# ---------- utilitários ----------
def _digitos(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    d = "".join(ch for ch in s if ch.isdigit())
    return d or None


def _checar_oficina(con, oficina_id: int, user: dict):
    o = db.um(con, "SELECT ID FROM OFICINA WHERE ID = %s AND EMPRESA_ID = %s", [oficina_id, user["empresa_id"]])
    if not o:
        raise HTTPException(status_code=404, detail="Oficina não encontrada")
    if user.get("oficina_id") and user["oficina_id"] != oficina_id:
        raise HTTPException(status_code=403, detail="Oficina fora do seu acesso")
