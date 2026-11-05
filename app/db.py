"""PostgreSQL access. All queries use %s placeholders, never string formatting."""
import os
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor
from flask import g


def connect():
    """Open a connection using the DB_* values from .env / the environment."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "grp01_appdb"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        cursor_factory=RealDictCursor,
    )


def get_db():
    if "db" not in g:
        g.db = connect()
    return g.db


def close_db(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.rollback()
        conn.close()


def init_app(app):
    app.teardown_appcontext(close_db)


def fetch_all(sql, params=()):
    with get_db().cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def fetch_one(sql, params=()):
    with get_db().cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()


@contextmanager
def tx():
    """One transaction: commits if the block finishes, rolls back if it raises."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
