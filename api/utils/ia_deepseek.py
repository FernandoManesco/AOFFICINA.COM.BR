# -*- coding: utf-8 -*-
"""Chamada mínima à API do DeepSeek (chat completions), sem SDK — portado do WebTriagem (v086).

.env:
  DEEPSEEK_API_KEY=...                 (obrigatório para as rotas /ia/*; sem ela o status avisa e as rotas devolvem 503)
  DEEPSEEK_MODEL=deepseek-chat         (opcional)
  CONTEXTO_IA_MD=contexto_oficina.md   (opcional; markdown de contexto lido a CADA chamada — editável sem reiniciar)

A API não tem memória: o contexto (quem somos, que texto é, regras) vai como mensagem de sistema em toda chamada.
O DeepSeek faz cache do prefixo repetido, então o custo do contexto é desprezível.
"""
import json
import logging
import os

import requests

logger = logging.getLogger(__name__)
URL = "https://api.deepseek.com/chat/completions"
_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # pasta api/


def _env(k, padrao=None):
    v = os.getenv(k)
    if v:
        return v
    try:
        for line in open(os.path.join(_RAIZ, ".env"), encoding="utf-8"):
            if line.startswith(k + "="):
                return line.split("=", 1)[1].strip().strip('"').strip("'") or padrao
    except OSError:
        pass
    return padrao


def disponivel() -> bool:
    return bool(_env("DEEPSEEK_API_KEY"))


def contexto() -> str:
    caminho = _env("CONTEXTO_IA_MD", "contexto_oficina.md")
    if not os.path.isabs(caminho):
        caminho = os.path.join(_RAIZ, caminho)
    try:
        return open(caminho, encoding="utf-8").read().strip()
    except OSError:
        logger.warning("contexto_oficina.md não encontrado em %s — usando contexto mínimo", caminho)
        return ("Você é o assistente técnico de uma oficina mecânica no Brasil. Responda em português do Brasil, de forma objetiva, "
                "sem inventar dados; quando não tiver certeza, diga que precisa de confirmação.")


def chat(mensagens, json_mode=False, temperatura=0.2, max_tokens=2000, timeout=90):
    chave = _env("DEEPSEEK_API_KEY")
    if not chave:
        raise RuntimeError("DEEPSEEK_API_KEY ausente no .env")
    corpo = {"model": _env("DEEPSEEK_MODEL", "deepseek-chat"), "messages": mensagens,
             "temperature": temperatura, "max_tokens": max_tokens, "stream": False}
    if json_mode:
        corpo["response_format"] = {"type": "json_object"}
    r = requests.post(URL, json=corpo, headers={"Authorization": "Bearer " + chave, "Content-Type": "application/json"}, timeout=timeout)
    if r.status_code >= 400:
        raise RuntimeError("DeepSeek HTTP %s: %s" % (r.status_code, r.text[:300]))
    dados = r.json()
    try:
        return dados["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise RuntimeError("DeepSeek: resposta sem conteúdo: %s" % json.dumps(dados)[:300])


def sem_cercas(t: str) -> str:
    t = (t or "").strip()
    if t.startswith("```"):
        linhas = t.split("\n")
        if linhas and linhas[0].startswith("```"):
            linhas = linhas[1:]
        if linhas and linhas[-1].strip().startswith("```"):
            linhas = linhas[:-1]
        t = "\n".join(linhas).strip()
    return t


def json_da_resposta(texto):
    t = sem_cercas(texto)
    if t.lower().startswith("json"):
        t = t[4:]
    ini, fim = t.find("{"), t.rfind("}")
    if ini >= 0 and fim > ini:
        t = t[ini:fim + 1]
    return json.loads(t)
