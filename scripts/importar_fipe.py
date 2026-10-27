#!/usr/bin/env python3
"""Importa marcas, modelos e anos (>= ANO_MINIMO) da API pública fipe.api.br para CAT_MARCA/CAT_MODELO/CAT_ANO.

Limites da API: 500 req/dia sem token, 1.000/dia com token grátis (FIPE_TOKEN no .env).
O script é retomável: modelos com ANOS_OK=1 não são consultados de novo; pode rodar todo dia
(cron) até terminar. Rodar na pasta api/:

    python3 ../scripts/importar_fipe.py --tipo carros            # dry-run (só lista marcas)
    python3 ../scripts/importar_fipe.py --tipo carros --commit   # importa, respeitando --max-req

Regra: só guardamos catálogo (marca/modelo/ano/combustível). Preço FIPE não é armazenado.
"""
import argparse
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "api"))
import config  # noqa: E402
import db      # noqa: E402

BASE = "https://fipe.parallelum.com.br/api/v2"
TIPOS = {"carros": ("cars", 1), "motos": ("motorcycles", 2), "caminhoes": ("trucks", 3)}
ANO_MINIMO = 2006   # últimos 20 anos
ANO_ZERO_KM = 32000  # código FIPE para "zero km" (ano corrente)


class Cliente:
    def __init__(self, max_req: int, pausa: float):
        self.s = requests.Session()
        if config.FIPE_TOKEN:
            self.s.headers["X-Subscription-Token"] = config.FIPE_TOKEN
        self.max_req, self.pausa, self.feitas = max_req, pausa, 0

    def get(self, caminho: str):
        if self.feitas >= self.max_req:
            raise RuntimeError(f"Limite de {self.max_req} requisições desta execução atingido — rode de novo amanhã/depois")
        self.feitas += 1
        for tent in range(3):
            r = self.s.get(f"{BASE}/{caminho}", timeout=30)
            if r.status_code == 429:
                time.sleep(30 * (tent + 1)); continue
            r.raise_for_status()
            time.sleep(self.pausa)
            return r.json()
        raise RuntimeError("API FIPE devolveu 429 repetidamente (limite diário)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tipo", choices=TIPOS.keys(), default="carros")
    ap.add_argument("--commit", action="store_true")
    ap.add_argument("--max-req", type=int, default=450, help="teto de requisições nesta execução (grátis: 500/dia)")
    ap.add_argument("--pausa", type=float, default=0.4, help="segundos entre requisições")
    args = ap.parse_args()

    recurso, tipo_num = TIPOS[args.tipo]
    api = Cliente(args.max_req, args.pausa)
    marcas = api.get(f"{recurso}/brands")
    print(f"{len(marcas)} marcas de {args.tipo} na FIPE.")
    if not args.commit:
        for m in marcas[:10]:
            print("  ", m["code"], m["name"])
        print("  ... (dry-run; use --commit para importar)")
        return

    with db.abrir() as con:
        ids_marca = {}
        for m in marcas:
            db.executar(con, "INSERT INTO CAT_MARCA (TIPO, CODIGO_FIPE, NOME) VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE NOME=VALUES(NOME)",
                        [tipo_num, m["code"], m["name"][:60]])
            ids_marca[m["code"]] = db.um(con, "SELECT ID FROM CAT_MARCA WHERE TIPO=%s AND CODIGO_FIPE=%s", [tipo_num, m["code"]])["ID"]
        con.commit()
        print("Marcas gravadas.")

        try:
            for m in marcas:
                marca_id = ids_marca[m["code"]]
                tem_modelos = db.um(con, "SELECT COUNT(*) N FROM CAT_MODELO WHERE MARCA_ID=%s", [marca_id])["N"]
                if not tem_modelos:
                    modelos = api.get(f"{recurso}/brands/{m['code']}/models")
                    for md in modelos:
                        db.executar(con, "INSERT IGNORE INTO CAT_MODELO (MARCA_ID, CODIGO_FIPE, NOME) VALUES (%s,%s,%s)",
                                    [marca_id, str(md["code"]), md["name"][:120]])
                    con.commit()
                    print(f"  {m['name']}: {len(modelos)} modelos")
                pend = db.todos(con, "SELECT ID, CODIGO_FIPE, NOME FROM CAT_MODELO WHERE MARCA_ID=%s AND ANOS_OK=0", [marca_id])
                for md in pend:
                    anos = api.get(f"{recurso}/brands/{m['code']}/models/{md['CODIGO_FIPE']}/years")
                    gravados = 0
                    for a in anos:
                        cod = a["code"]                      # ex. "2014-3" ou "32000-1"
                        ano_txt = cod.split("-")[0]
                        ano = time.localtime().tm_year if ano_txt == str(ANO_ZERO_KM) else int(ano_txt)
                        if ano < ANO_MINIMO:
                            continue
                        comb = a["name"].split(" ", 1)[1] if " " in a["name"] else None
                        db.executar(con, "INSERT IGNORE INTO CAT_ANO (MODELO_ID, CODIGO_FIPE, ANO, COMBUSTIVEL) VALUES (%s,%s,%s,%s)",
                                    [md["ID"], cod, ano, (comb or "")[:20] or None])
                        gravados += 1
                    db.executar(con, "UPDATE CAT_MODELO SET ANOS_OK=1 WHERE ID=%s", [md["ID"]])
                    con.commit()
                # modelos sem nenhum ano >= 2006 ficam no catálogo mas sem anos (busca ainda acha)
        except RuntimeError as e:
            con.commit()
            print(f"\nPARADO: {e}")
            print("Progresso salvo. Rode de novo para continuar.")
            return

    with db.abrir() as con:
        r = db.um(con, """SELECT (SELECT COUNT(*) FROM CAT_MODELO D JOIN CAT_MARCA M ON M.ID=D.MARCA_ID WHERE M.TIPO=%s AND D.ANOS_OK=0) PEND,
                                 (SELECT COUNT(*) FROM CAT_MODELO D JOIN CAT_MARCA M ON M.ID=D.MARCA_ID WHERE M.TIPO=%s) TOT""",
                  [tipo_num, tipo_num])
    print(f"\nRequisições usadas: {api.feitas}. Modelos: {r['TOT']} total, {r['PEND']} ainda sem anos.")
    print("Concluído." if r["PEND"] == 0 else "Rode novamente para continuar.")


if __name__ == "__main__":
    main()
