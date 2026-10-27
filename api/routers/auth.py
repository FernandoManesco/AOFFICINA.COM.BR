"""Login, dados do usuário logado e troca de senha."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

import db
from utils.auth import (criar_token, hash_senha, ip_do_request, security_log,
                        usuario_atual, verificar_senha)

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)


class LoginIn(BaseModel):
    login: str = Field(min_length=2, max_length=60)
    senha: str = Field(min_length=1, max_length=100)


class TrocaSenhaIn(BaseModel):
    senha_atual: str
    senha_nova: str = Field(min_length=8, max_length=100)


@router.post("/login")  # PUBLICA: é o login (ver config.ROTAS_PUBLICAS)
@limiter.limit("10/minute")
def login(request: Request, dados: LoginIn, con=Depends(db.get_db_dep)):
    ip = ip_do_request(request)
    u = db.um(con, "SELECT ID id, EMPRESA_ID empresa_id, OFICINA_ID oficina_id, NOME nome, LOGIN login, "
                   "SENHA_HASH senha_hash, NIVEL nivel, PRIMEIRO_ACESSO primeiro_acesso, ATIVO ativo "
                   "FROM USUARIO WHERE LOGIN = %s", [dados.login.strip().lower()])
    if not u or not u["ativo"] or not verificar_senha(dados.senha, u["senha_hash"]):
        security_log(con, "LOGIN_FALHA", dados.login, ip)
        con.commit()  # exceção única ao "sem commit no router": o log de falha precisa sobreviver ao rollback
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos")
    db.executar(con, "UPDATE USUARIO SET ULTIMO_LOGIN = %s WHERE ID = %s", [datetime.utcnow(), u["id"]])
    security_log(con, "LOGIN_OK", u["login"], ip)
    return {
        "token": criar_token(u),
        "nome": u["nome"],
        "nivel": int(u["nivel"]),
        "empresa_id": u["empresa_id"],
        "oficina_id": u["oficina_id"],
        "primeiro_acesso": bool(u["primeiro_acesso"]),
    }


@router.get("/me")
def me(user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    u = db.um(con, "SELECT U.ID id, U.NOME nome, U.LOGIN login, U.EMAIL email, U.NIVEL nivel, "
                   "U.OFICINA_ID oficina_id, O.NOME oficina_nome, E.FANTASIA empresa_fantasia "
                   "FROM USUARIO U JOIN EMPRESA E ON E.ID = U.EMPRESA_ID "
                   "LEFT JOIN OFICINA O ON O.ID = U.OFICINA_ID WHERE U.ID = %s", [user["sub"]])
    if not u:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return u


@router.post("/trocar-senha")
def trocar_senha(request: Request, dados: TrocaSenhaIn, user=Depends(usuario_atual), con=Depends(db.get_db_dep)):
    u = db.um(con, "SELECT LOGIN login, SENHA_HASH senha_hash FROM USUARIO WHERE ID = %s", [user["sub"]])
    if not u or not verificar_senha(dados.senha_atual, u["senha_hash"]):
        security_log(con, "TROCA_SENHA_FALHA", u["login"] if u else None, ip_do_request(request))
        con.commit()
        raise HTTPException(status_code=400, detail="Senha atual incorreta")
    db.executar(con, "UPDATE USUARIO SET SENHA_HASH = %s, PRIMEIRO_ACESSO = 0 WHERE ID = %s",
                [hash_senha(dados.senha_nova), user["sub"]])
    security_log(con, "TROCA_SENHA_OK", u["login"], ip_do_request(request))
    return {"ok": True}
