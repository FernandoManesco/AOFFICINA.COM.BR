#!/usr/bin/env python3
"""Cria a empresa, a primeira oficina e o usuário administrador (nível 0) de uma instância nova.

Rodar na pasta api/ (para ler o .env), com a migration já aplicada:
    python3 ../scripts/criar_instancia.py            # dry-run: mostra o que faria
    python3 ../scripts/criar_instancia.py --commit   # grava (pede a senha do admin no terminal)

Idempotente: se já existir EMPRESA, só avisa e sai.
"""
import argparse
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "api"))

import db                      # noqa: E402
from utils.auth import hash_senha  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true")
    ap.add_argument("--razao", default="Oficina Demonstração Ltda")
    ap.add_argument("--fantasia", default="aOfficina Demo")
    ap.add_argument("--oficina", default="Matriz")
    ap.add_argument("--admin-nome", default="Fernando Manesco")
    ap.add_argument("--admin-login", default="fernando")
    args = ap.parse_args()

    with db.abrir() as con:
        if db.um(con, "SELECT ID FROM EMPRESA LIMIT 1"):
            print("Já existe EMPRESA nesta instância — nada a fazer.")
            return
        print(f"Empresa: {args.razao} ({args.fantasia}) | Oficina: {args.oficina} | Admin: {args.admin_login}")
        if not args.commit:
            print("Dry-run. Para gravar: acrescente --commit")
            return
        senha = getpass.getpass("Senha do admin (mín. 8): ")
        if len(senha) < 8 or senha != getpass.getpass("Repita a senha: "):
            print("Senha inválida ou diferente. Abortado.")
            sys.exit(1)
        emp = db.executar(con, "INSERT INTO EMPRESA (RAZAO_SOCIAL, FANTASIA) VALUES (%s, %s)", [args.razao, args.fantasia])
        ofi = db.executar(con, "INSERT INTO OFICINA (EMPRESA_ID, NOME) VALUES (%s, %s)", [emp, args.oficina])
        for i in (1, 2):
            db.executar(con, "INSERT INTO EQUIPAMENTO (OFICINA_ID, NOME, TIPO) VALUES (%s, %s, 'ELEVADOR')", [ofi, f"Elevador {i}"])
        db.executar(con, """INSERT INTO USUARIO (EMPRESA_ID, OFICINA_ID, NOME, LOGIN, SENHA_HASH, NIVEL, PRIMEIRO_ACESSO)
                            VALUES (%s, NULL, %s, %s, %s, 0, 0)""",
                    [emp, args.admin_nome, args.admin_login.lower(), hash_senha(senha)])
        print(f"OK: EMPRESA {emp}, OFICINA {ofi}, 2 elevadores, admin '{args.admin_login}' criado.")


if __name__ == "__main__":
    main()
