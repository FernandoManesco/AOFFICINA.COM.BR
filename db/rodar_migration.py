#!/usr/bin/env python3
"""Aplica as migrations de db/migrations/ no MySQL da instância.

Uso (na pasta api/, para enxergar o .env):
    python3 ../db/rodar_migration.py            # dry-run: mostra o que faria
    python3 ../db/rodar_migration.py --commit   # aplica

Regras: idempotente (controle em SCHEMA_MIGRATIONS), um arquivo vNNN_nome.sql
por versão, statements separados por ';' no fim da linha. Não usar DELIMITER
(sem triggers/procedures nos arquivos — regra de simplicidade).
"""
import argparse
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "api"))

import pymysql  # noqa: E402
import config   # noqa: E402

PASTA = AQUI / "migrations"


def listar_arquivos():
    arqs = sorted(PASTA.glob("v[0-9][0-9][0-9]_*.sql"))
    return [(a.name[:4], a) for a in arqs]


def statements(texto: str):
    sem_coment = "\n".join(l for l in texto.splitlines() if not l.strip().startswith("--"))
    for st in re.split(r";\s*\n", sem_coment):
        st = st.strip()
        if st:
            yield st


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true", help="aplica de verdade (padrão: dry-run)")
    args = ap.parse_args()

    con = pymysql.connect(
        host=config.DB_HOST, port=config.DB_PORT, user=config.DB_USER,
        password=config.DB_PASSWORD, database=config.DB_NAME,
        charset="utf8mb4", autocommit=False,
    )
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS SCHEMA_MIGRATIONS (VERSAO VARCHAR(10) NOT NULL PRIMARY KEY, "
                "NOME VARCHAR(120) NOT NULL, APLICADO_EM DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP) "
                "ENGINE=InnoDB DEFAULT CHARSET=utf8mb4")
    con.commit()
    cur.execute("SELECT VERSAO FROM SCHEMA_MIGRATIONS")
    aplicadas = {r[0] for r in cur.fetchall()}

    pendentes = [(v, a) for v, a in listar_arquivos() if v not in aplicadas]
    print(f"Banco: {config.DB_NAME}@{config.DB_HOST}  |  aplicadas: {sorted(aplicadas) or '-'}")
    if not pendentes:
        print("Nada pendente.")
        return
    for v, a in pendentes:
        print(f"{'APLICANDO' if args.commit else 'DRY-RUN '} {a.name}")
        if not args.commit:
            continue
        try:
            for st in statements(a.read_text(encoding="utf-8")):
                cur.execute(st)
            cur.execute("INSERT INTO SCHEMA_MIGRATIONS (VERSAO, NOME) VALUES (%s, %s)", (v, a.name))
            con.commit()
            print(f"  ok {a.name}")
        except Exception as e:
            con.rollback()
            print(f"  ERRO em {a.name}: {e}")
            sys.exit(1)
    if not args.commit:
        print("\nDry-run. Para aplicar: python3 ../db/rodar_migration.py --commit")


if __name__ == "__main__":
    main()
