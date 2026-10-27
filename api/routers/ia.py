"""Assistente de IA do aOfficina — portado do WebTriagem (triagem_ia.py v086) e adaptado à oficina.

GET  /ia/status                 {deepseek, whisper, myscript, modelo}
GET  /ia/escrita/config         chaves do MyScript iink (só para usuário logado; nunca ficam no HTML)
POST /ia/transcrever            multipart (audio, campo) -> {texto, duracao, segundos}   (faster-whisper no servidor)
POST /ia/corrigir               {campo, texto} -> {texto}         corrige/formata um campo (DeepSeek + contexto_oficina.md)
POST /ia/pesquisar              {tipo: problema|peca, texto, veiculo{...}, km} -> {resposta}   pesquisa técnica
"""
from __future__ import annotations

import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from utils import ia_deepseek as ia
from utils import transcricao
from utils.auth import requer_nivel, usuario_atual

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ia", tags=["ia"], dependencies=[Depends(requer_nivel(3))])

CAMPOS = {
    "queixa": "Queixa do cliente",
    "diagnostico": "Diagnóstico do mecânico",
    "descricao_executado": "Descrição do serviço executado",
    "servico_descricao": "Descrição padrão do serviço (cadastro de mão de obra)",
    "observacao": "Observações do pedido",
    "aplicacao": "Aplicação da peça (veículos compatíveis)",
}


@router.get("/status")
def status():
    return {"deepseek": ia.disponivel(), "whisper": transcricao.disponivel(),
            "myscript": bool(ia._env("MYSCRIPT_APP_KEY") and ia._env("MYSCRIPT_HMAC_KEY")),
            "modelo": ia._env("DEEPSEEK_MODEL", "deepseek-chat"), "whisper_modelo": ia._env("WHISPER_MODELO", "small"),
            "contexto_bytes": len(ia.contexto())}


@router.get("/escrita/config")
def escrita_config():
    app_key, hmac = ia._env("MYSCRIPT_APP_KEY"), ia._env("MYSCRIPT_HMAC_KEY")
    if not app_key or not hmac:
        raise HTTPException(503, "Escrita à mão não configurada (MYSCRIPT_APP_KEY / MYSCRIPT_HMAC_KEY no .env)")
    return {"applicationKey": app_key, "hmacKey": hmac, "lang": ia._env("MYSCRIPT_LANG", "pt_BR")}


AUDIO_MAX = 25 * 1024 * 1024
_SUFIXO = {"audio/webm": ".webm", "video/webm": ".webm", "audio/ogg": ".ogg", "audio/mp4": ".m4a", "audio/x-m4a": ".m4a",
           "audio/mpeg": ".mp3", "audio/wav": ".wav", "audio/x-wav": ".wav", "audio/flac": ".flac"}


@router.post("/transcrever")
def transcrever(audio: UploadFile = File(...), campo: str = Form(""), user=Depends(usuario_atual)):
    if not transcricao.disponivel():
        raise HTTPException(503, "Ditado no servidor não instalado (faster-whisper). Use o Chrome/Edge, que reconhece a voz no próprio navegador.")
    dados = audio.file.read(AUDIO_MAX + 1)
    if not dados:
        raise HTTPException(422, "Áudio vazio")
    if len(dados) > AUDIO_MAX:
        raise HTTPException(413, "Áudio muito longo (máximo ~20 minutos)")
    tipo = (audio.content_type or "").split(";")[0].strip().lower()
    sufixo = _SUFIXO.get(tipo) or ((os.path.splitext(audio.filename or "")[1] or ".webm").lower())
    prompt = "Oficina mecânica, " + (CAMPOS.get(campo, "anotação técnica") + ": peças, freio, suspensão, motor, injeção, óleo, km.")
    try:
        r = transcricao.transcrever(dados, sufixo, prompt)
    except Exception as e:  # noqa: BLE001
        logger.exception("ia/transcrever")
        raise HTTPException(502, "Transcrição falhou: %s" % str(e)[:200])
    logger.info("transcrever %s: %.1fs de áudio em %.1fs (%s)", campo, r["duracao"], r["segundos"], user.get("nome"))
    return {"campo": campo, **r}


class CorrigirIn(BaseModel):
    campo: str = Field(..., max_length=30)
    texto: str = Field(..., min_length=1, max_length=8000)


@router.post("/corrigir")
def corrigir(d: CorrigirIn, user=Depends(usuario_atual)):
    if d.campo not in CAMPOS:
        raise HTTPException(422, "Campo inválido")
    if not ia.disponivel():
        raise HTTPException(503, "IA não configurada (DEEPSEEK_API_KEY no .env)")
    pedido = ("TAREFA: corrigir e formatar o texto do campo \"%s\" (%s), seguindo as regras do contexto para esse campo. "
              "Devolva SOMENTE o texto final, sem explicações nem aspas.\n\nTEXTO BRUTO:\n%s" % (CAMPOS[d.campo], d.campo, d.texto.strip()))
    try:
        saida = ia.chat([{"role": "system", "content": ia.contexto()}, {"role": "user", "content": pedido}])
    except Exception as e:  # noqa: BLE001
        logger.exception("ia/corrigir")
        raise HTTPException(502, "IA indisponível: %s" % str(e)[:200])
    return {"campo": d.campo, "texto": ia.sem_cercas(saida)}


class Veiculo(BaseModel):
    marca: Optional[str] = None
    modelo: Optional[str] = None
    ano: Optional[int] = None
    combustivel: Optional[str] = None


class PesquisarIn(BaseModel):
    tipo: str = Field(..., pattern="^(problema|peca)$")
    texto: str = Field(..., min_length=3, max_length=4000)
    veiculo: Veiculo = Veiculo()
    km: Optional[int] = None


@router.post("/pesquisar")
def pesquisar(d: PesquisarIn, user=Depends(usuario_atual)):
    """problema: sintoma -> causas prováveis e como verificar. peca: peça -> nome técnico, variantes, fabricantes, referências."""
    if not ia.disponivel():
        raise HTTPException(503, "IA não configurada (DEEPSEEK_API_KEY no .env)")
    v = d.veiculo
    desc_v = " ".join(str(x) for x in [v.marca, v.modelo, v.ano, v.combustivel] if x) or "veículo não informado"
    if d.tipo == "problema":
        pedido = ("TAREFA: pesquisa de problema. Veículo: %s%s.\nSINTOMA / RELATO:\n%s\n\n"
                  "Responda conforme a seção 'Pesquisa de problema' do contexto, em markdown simples." % (desc_v, f", {d.km} km" if d.km else "", d.texto.strip()))
    else:
        pedido = ("TAREFA: pesquisa de código de peça. Veículo: %s.\nPEÇA DESEJADA:\n%s\n\n"
                  "Responda conforme a seção 'Pesquisa de código de peça' do contexto, em markdown simples." % (desc_v, d.texto.strip()))
    try:
        saida = ia.chat([{"role": "system", "content": ia.contexto()}, {"role": "user", "content": pedido}], temperatura=0.3, max_tokens=1500)
    except Exception as e:  # noqa: BLE001
        logger.exception("ia/pesquisar")
        raise HTTPException(502, "IA indisponível: %s" % str(e)[:200])
    return {"tipo": d.tipo, "resposta": ia.sem_cercas(saida)}
