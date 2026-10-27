# -*- coding: utf-8 -*-
"""Transcrição de áudio no próprio servidor com faster-whisper (CPU por padrão) — portado do WebTriagem (v086b).
A página grava o áudio (MediaRecorder) e envia; nada vai para o Google. Funciona em qualquer navegador.

Instalação (opcional — só se for usar o ditado fora do Chrome/Edge/Safari):
  .venv/bin/pip install -r requirements-ia.txt     e     python3 ../scripts/baixar_modelo_whisper.py

.env (opcionais):
  WHISPER_MODELO=small   WHISPER_DEVICE=cpu   WHISPER_COMPUTE=int8   WHISPER_THREADS=4
  WHISPER_CACHE=/home/deploy/modelos/whisper   (mesma pasta do WebTriagem — o modelo é compartilhado)
"""
from __future__ import annotations

import logging
import os
import tempfile
import threading
import time

logger = logging.getLogger(__name__)
_modelo = None
_lock = threading.Lock()
_carga = threading.Lock()


def _env(k, d=None):
    v = os.getenv(k)
    return v if v not in (None, "") else d


def disponivel() -> bool:
    try:
        import faster_whisper  # noqa: F401
        return True
    except Exception:  # noqa: BLE001
        return False


def modelo():
    global _modelo
    if _modelo is not None:
        return _modelo
    with _carga:
        if _modelo is None:
            from faster_whisper import WhisperModel
            nome = _env("WHISPER_MODELO", "small")
            t = time.time()
            _modelo = WhisperModel(nome, device=_env("WHISPER_DEVICE", "cpu"), compute_type=_env("WHISPER_COMPUTE", "int8"),
                                   cpu_threads=int(_env("WHISPER_THREADS", "4")), download_root=_env("WHISPER_CACHE", "/home/deploy/modelos/whisper"))
            logger.info("whisper %s carregado em %.1fs", nome, time.time() - t)
    return _modelo


def transcrever(dados: bytes, sufixo: str = ".webm", prompt: str = "") -> dict:
    m = modelo()
    with tempfile.NamedTemporaryFile(suffix=sufixo or ".webm", delete=False) as f:
        f.write(dados)
        caminho = f.name
    try:
        t = time.time()
        with _lock:
            try:
                segs, info = m.transcribe(caminho, language="pt", beam_size=5, vad_filter=True,
                                          vad_parameters={"min_silence_duration_ms": 400}, initial_prompt=prompt or None)
                partes = [s.text.strip() for s in segs if s.text and s.text.strip()]
            except Exception as e:  # noqa: BLE001
                logger.warning("transcrição sem VAD: %s", str(e)[:120])
                segs, info = m.transcribe(caminho, language="pt", beam_size=5, initial_prompt=prompt or None)
                partes = [s.text.strip() for s in segs if s.text and s.text.strip()]
        return {"texto": " ".join(partes).strip(), "duracao": round(float(info.duration or 0), 1), "segundos": round(time.time() - t, 1)}
    finally:
        try:
            os.unlink(caminho)
        except OSError:
            pass
