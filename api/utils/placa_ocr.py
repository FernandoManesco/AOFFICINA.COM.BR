# -*- coding: utf-8 -*-
"""Leitura de placa brasileira a partir de uma foto (OCR local com Tesseract, sem enviar imagem para fora).

Instalação no servidor (uma vez):
    sudo apt install -y tesseract-ocr
    .venv/bin/pip install pytesseract Pillow

A página já manda a imagem recortada pela moldura; aqui só melhoramos o contraste, tentamos algumas variações
e procuramos o padrão ABC1234 (antiga) ou ABC1D23 (Mercosul). Devolve a lista de candidatas em ordem de confiança.
"""
from __future__ import annotations

import io
import re
from typing import List

RE_PLACA = re.compile(r"[A-Z]{3}[0-9][A-Z0-9][0-9]{2}")
# confusões típicas do OCR, aplicadas por posição (letra x dígito)
L2D = str.maketrans({"O": "0", "Q": "0", "D": "0", "I": "1", "L": "1", "Z": "2", "S": "5", "B": "8", "G": "6", "T": "7"})
D2L = str.maketrans({"0": "O", "1": "I", "2": "Z", "5": "S", "8": "B", "6": "G", "7": "T", "4": "A"})


def disponivel() -> bool:
    try:
        import pytesseract  # noqa: F401
        from PIL import Image  # noqa: F401
        pytesseract.get_tesseract_version()
        return True
    except Exception:  # noqa: BLE001
        return False


def _normalizar(txt: str) -> List[str]:
    """Gera candidatas a placa a partir de um texto bruto do OCR."""
    bruto = re.sub(r"[^A-Z0-9]", "", txt.upper())
    cands = []
    for m in RE_PLACA.finditer(bruto):
        cands.append(m.group(0))
    # tenta corrigir confusões em janelas de 7 caracteres
    for i in range(0, max(0, len(bruto) - 6)):
        j = bruto[i:i + 7]
        fix = j[:3].translate(D2L) + j[3].translate(L2D) + j[4] + j[5:].translate(L2D)
        if RE_PLACA.fullmatch(fix):
            cands.append(fix)
        fix2 = j[:3].translate(D2L) + j[3].translate(L2D) + j[4].translate(L2D) + j[5:].translate(L2D)  # antiga
        if RE_PLACA.fullmatch(fix2):
            cands.append(fix2)
    vistos, saida = set(), []
    for c in cands:
        if c not in vistos:
            vistos.add(c); saida.append(c)
    return saida


def ler(dados: bytes) -> dict:
    import pytesseract
    from PIL import Image, ImageOps, ImageFilter

    im = Image.open(io.BytesIO(dados)).convert("L")
    if im.width < 600:
        im = im.resize((im.width * 2, im.height * 2), Image.LANCZOS)
    im = ImageOps.autocontrast(im, cutoff=2)
    variantes = [im, im.filter(ImageFilter.SHARPEN), im.point(lambda p: 255 if p > 140 else 0), ImageOps.invert(im).point(lambda p: 255 if p > 140 else 0)]
    cfg = "--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    textos, cands = [], []
    for v in variantes:
        for psm in ("7", "6"):
            try:
                t = pytesseract.image_to_string(v, lang="eng", config=cfg.replace("--psm 7", f"--psm {psm}"))
            except Exception:  # noqa: BLE001
                continue
            t = t.strip()
            if t:
                textos.append(t)
                for c in _normalizar(t):
                    if c not in cands:
                        cands.append(c)
            if len(cands) >= 3:
                break
        if len(cands) >= 3:
            break
    return {"placas": cands[:3], "texto": " | ".join(textos)[:200]}
