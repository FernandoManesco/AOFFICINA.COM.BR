"""Acesso ao MySQL via PyMySQL.

Padrão igual ao nfe-servico: os routers usam `get_db_dep` e NÃO fazem
commit/rollback — o context manager commita se tudo deu certo e desfaz se
houve exceção. Cursor retorna dicionários (DictCursor).

Convenções:
- valores monetários em centavos (BIGINT), nunca float;
- datas em tipo DATE/DATETIME nativo (MySQL aceita 'YYYY-MM-DD');
- SQL sempre parametrizado com %s.
"""
from contextlib import contextmanager
from typing import Generator

import pymysql
import pymysql.cursors
from pymysql.constants import CLIENT

import config


def conectar() -> pymysql.connections.Connection:
    return pymysql.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        client_flag=CLIENT.FOUND_ROWS,  # UPDATE devolve linhas ENCONTRADAS, não só alteradas (senão 'salvar sem mudar nada' vira 404)
        connect_timeout=5,
        read_timeout=30,
        write_timeout=30,
    )


@contextmanager
def abrir() -> Generator[pymysql.connections.Connection, None, None]:
    con = conectar()
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def get_db_dep():
    """Dependência FastAPI: `db: Connection = Depends(get_db_dep)`."""
    with abrir() as con:
        yield con


def um(con, sql: str, params=None):
    with con.cursor() as cur:
        cur.execute(sql, params or [])
        return cur.fetchone()


def todos(con, sql: str, params=None):
    with con.cursor() as cur:
        cur.execute(sql, params or [])
        return cur.fetchall()


def executar(con, sql: str, params=None) -> int:
    """Executa INSERT/UPDATE/DELETE e devolve lastrowid (ou linhas afetadas)."""
    with con.cursor() as cur:
        afetadas = cur.execute(sql, params or [])
        return cur.lastrowid or afetadas
