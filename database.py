import os
from contextlib import contextmanager

import psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


@contextmanager
def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is missing. Add your PostgreSQL connection string to .env.")

    conn = psycopg.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    post_url TEXT PRIMARY KEY,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        conn.commit()


def exists(url):
    if not url:
        return False

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM jobs WHERE post_url = %s",
                (url,),
            )
            return cursor.fetchone() is not None


def claim(url):
    if not url:
        return False

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO jobs(post_url)
                VALUES(%s)
                ON CONFLICT DO NOTHING
                RETURNING post_url
                """,
                (url,),
            )
            inserted = cursor.fetchone() is not None
        conn.commit()
        return inserted


def save(url):
    if not url:
        return

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO jobs(post_url) VALUES(%s) ON CONFLICT DO NOTHING",
                (url,),
            )
        conn.commit()
