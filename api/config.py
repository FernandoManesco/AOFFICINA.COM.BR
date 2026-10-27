"""Configuração central — lê o .env e falha no boot se faltar segredo (regra 5)."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _obrigatoria(nome: str) -> str:
    valor = os.getenv(nome, "").strip()
    if not valor:
        raise RuntimeError(f"Variável obrigatória ausente no .env: {nome}")
    return valor


INSTANCIA = os.getenv("INSTANCIA", "aofficina")
AMBIENTE = os.getenv("AMBIENTE", "producao")

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = _obrigatoria("DB_NAME")
DB_USER = _obrigatoria("DB_USER")
DB_PASSWORD = _obrigatoria("DB_PASSWORD")

SECRET_KEY = _obrigatoria("SECRET_KEY")
if len(SECRET_KEY) < 32:
    raise RuntimeError("SECRET_KEY precisa ter pelo menos 32 caracteres")
JWT_ALG = "HS256"
JWT_EXPIRA_MIN = int(os.getenv("JWT_EXPIRA_MIN", "600"))

CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
FIPE_TOKEN = os.getenv("FIPE_TOKEN", "").strip()

# Rotas que não exigem token (regra 1: exceção explícita e justificada)
ROTAS_PUBLICAS = {
    "/",                 # PUBLICA: healthcheck
    "/health",           # PUBLICA: healthcheck do monitor/nginx
    "/auth/login",       # PUBLICA: é o próprio login
    "/docs", "/openapi.json", "/redoc",  # PUBLICA: só em AMBIENTE=dev (ver main.py)
}
