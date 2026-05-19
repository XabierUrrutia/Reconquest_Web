import os
import secrets
import logging
import psycopg2
import psycopg2.extras
from flask import g

from .config import DATABASE_URL
from .utils import _now, _hash_pwd


def get_db():
    if "db" not in g:
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
        conn.autocommit = False
        g.db = conn
    return g.db


def db_execute(query, params=()):
    """Ejecuta una query y devuelve el cursor."""
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    query = query.replace("?", "%s")
    cur.execute(query, params)
    return cur


def db_fetchone(query, params=()):
    cur = db_execute(query, params)
    return cur.fetchone()


def db_fetchall(query, params=()):
    cur = db_execute(query, params)
    return cur.fetchall()


def db_commit():
    get_db().commit()


def close_db(exc):
    db = g.pop("db", None)
    if db:
        if exc:
            db.rollback()
        db.close()


def init_db():
    conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
    cur  = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          SERIAL PRIMARY KEY,
            username    TEXT    NOT NULL UNIQUE,
            email       TEXT    NOT NULL UNIQUE,
            password    TEXT    NOT NULL,
            salt        TEXT    NOT NULL,
            is_admin    INTEGER NOT NULL DEFAULT 0,
            is_active   INTEGER NOT NULL DEFAULT 1,
            created_at  TEXT    NOT NULL,
            last_login  TEXT,
            avatar_url  TEXT
        );
        CREATE TABLE IF NOT EXISTS reset_tokens (
            id         SERIAL PRIMARY KEY,
            user_id    INTEGER NOT NULL,
            token      TEXT    NOT NULL UNIQUE,
            expires_at TEXT    NOT NULL,
            used       INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS download_log (
            id         SERIAL PRIMARY KEY,
            user_id    INTEGER,
            ip         TEXT,
            user_agent TEXT,
            ts         TEXT    NOT NULL
        );
        CREATE TABLE IF NOT EXISTS bug_reports (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER,
            description TEXT    NOT NULL,
            created_at  TEXT    NOT NULL
        );
        CREATE TABLE IF NOT EXISTS reviews (
            id         SERIAL PRIMARY KEY,
            user_id    INTEGER NOT NULL,
            rating     INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
            body       TEXT    NOT NULL,
            approved   INTEGER NOT NULL DEFAULT 0,
            created_at TEXT    NOT NULL
        );
    """)
    cur.execute("SELECT id FROM users WHERE is_admin=1 LIMIT 1")
    if not cur.fetchone():
        admin_password = os.environ.get("ADMIN_PASSWORD")
        if not admin_password:
            admin_password = secrets.token_urlsafe(16)
            logging.warning(
                "ADMIN_PASSWORD no configurada. Password de admin generada: %s — "
                "guárdala ahora, no se volverá a mostrar.",
                admin_password
            )
        pwd = _hash_pwd(admin_password)
        cur.execute(
            "INSERT INTO users (username,email,password,salt,is_admin,created_at) VALUES (%s,%s,%s,%s,1,%s)",
            ("admin", "admin@reconquest.local", pwd, "", _now())
        )
    conn.commit()
    conn.close()
