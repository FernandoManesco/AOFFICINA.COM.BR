"""aOfficina — API (FastAPI). Porta 8300, atrás do Nginx em api.aofficina.com.br.

Toda rota nasce autenticada (middleware JWT); exceções em config.ROTAS_PUBLICAS.
"""
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

import config
from utils.auth import decodificar_token
from routers import auth, empresa, clientes, veiculos, catalogo, agenda, pecas, servicos, pedidos, ia

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("aofficina")

dev = config.AMBIENTE == "dev"
app = FastAPI(
    title="aOfficina API",
    version="0.3.0",
    docs_url="/docs" if dev else None,
    redoc_url=None,
    openapi_url="/openapi.json" if dev else None,
)

limiter = Limiter(key_func=get_remote_address, default_limits=["600/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS or ["http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def autenticar(request: Request, call_next):
    caminho = request.url.path.rstrip("/") or "/"
    if request.method == "OPTIONS" or caminho in config.ROTAS_PUBLICAS:
        return await call_next(request)
    cab = request.headers.get("authorization", "")
    if not cab.lower().startswith("bearer "):
        return JSONResponse({"detail": "Não autenticado"}, status_code=401)
    try:
        request.state.user = decodificar_token(cab[7:].strip())
    except Exception as e:  # HTTPException do decodificar_token
        return JSONResponse({"detail": getattr(e, "detail", "Token inválido")}, status_code=401)
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    return resp


@app.get("/")
@app.get("/health")
def health():
    return {"ok": True, "app": "aofficina", "instancia": config.INSTANCIA}


for r in (auth.router, empresa.router, clientes.router, veiculos.router, catalogo.router, agenda.router,
          pecas.router, servicos.router, pedidos.router, ia.router):
    app.include_router(r)

log.info("Rotas registradas: %d", len(app.routes))
