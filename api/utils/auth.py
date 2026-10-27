"""Autenticação JWT + níveis de acesso + log de segurança.

Níveis do aOfficina (USUARIO.NIVEL):
  0 = Dono / administrador (tudo, inclusive usuários e configuração)
  1 = Gerente da oficina (cadastros, OS, estoque, financeiro, relatórios)
  2 = Atendente / recepção (clientes, veículos, fila, abrir OS, receber)
  3 = Mecânico (fila, diagnóstico, itens da própria OS)
  4 = Financeiro (contas a pagar/receber, caixa, sem cadastros operacionais)

`requer_nivel(n)` libera quem tem nível <= n (0 é o mais alto).
"""
from datetime import datetime, timedelta
from typing import Iterable, Optional

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt
from passlib.context import CryptContext

import config
import db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_senha(senha: str) -> str:
    return pwd_context.hash(senha)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        return pwd_context.verify(senha, senha_hash)
    except Exception:
        return False


def criar_token(usuario: dict) -> str:
    agora = datetime.utcnow()
    claims = {
        "sub": str(usuario["id"]),
        "nome": usuario["nome"],
        "nivel": int(usuario["nivel"]),
        "empresa_id": int(usuario["empresa_id"]),
        "oficina_id": usuario.get("oficina_id"),
        "primeiro_acesso": bool(usuario.get("primeiro_acesso")),
        "iat": agora,
        "exp": agora + timedelta(minutes=config.JWT_EXPIRA_MIN),
    }
    return jwt.encode(claims, config.SECRET_KEY, algorithm=config.JWT_ALG)


def decodificar_token(token: str) -> dict:
    try:
        return jwt.decode(token, config.SECRET_KEY, algorithms=[config.JWT_ALG])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido ou expirado")


def usuario_atual(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return user


def requer_nivel(nivel_maximo: int):
    """Dependência: só passa quem tem nível <= nivel_maximo."""
    def _dep(user: dict = Depends(usuario_atual)) -> dict:
        if int(user.get("nivel", 99)) > nivel_maximo:
            raise HTTPException(status_code=403, detail="Sem permissão para esta operação")
        return user
    return _dep


def requer_niveis(niveis: Iterable[int]):
    permitidos = set(int(n) for n in niveis)
    def _dep(user: dict = Depends(usuario_atual)) -> dict:
        if int(user.get("nivel", 99)) not in permitidos:
            raise HTTPException(status_code=403, detail="Sem permissão para esta operação")
        return user
    return _dep


def ip_do_request(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()[:45]
    return (request.client.host if request.client else "")[:45]


def security_log(con, evento: str, login: Optional[str], ip: str, detalhe: str = ""):
    """Regra 9: registra sucesso/falha de login e ações sensíveis."""
    db.executar(
        con,
        "INSERT INTO SECURITY_LOG (EVENTO, LOGIN, IP, DETALHE) VALUES (%s, %s, %s, %s)",
        [evento[:40], (login or "")[:60], ip[:45], detalhe[:255]],
    )
