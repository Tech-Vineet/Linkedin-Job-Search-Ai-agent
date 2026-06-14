import os
from contextlib import contextmanager
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


@contextmanager
def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is missing. Add your PostgreSQL connection string to .env.")

    conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
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
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS application_drafts (
                    id TEXT PRIMARY KEY,
                    post_url TEXT NOT NULL,
                    hr_email TEXT NOT NULL,
                    company TEXT NOT NULL DEFAULT '',
                    role TEXT NOT NULL DEFAULT '',
                    subject TEXT NOT NULL,
                    body TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    decided_at TIMESTAMPTZ,
                    sent_at TIMESTAMPTZ
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


def create_application_draft(post_url, hr_email, company, role, subject, body):
    draft_id = str(uuid4())

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO application_drafts(
                    id, post_url, hr_email, company, role, subject, body
                )
                VALUES(%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, post_url, hr_email, company, role, subject, body, status
                """,
                (draft_id, post_url, hr_email, company or "", role or "", subject, body),
            )
            draft = cursor.fetchone()
        conn.commit()
        return draft


def get_pending_application_draft(draft_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, post_url, hr_email, company, role, subject, body, status
                FROM application_drafts
                WHERE id = %s AND status = 'pending'
                """,
                (draft_id,),
            )
            return cursor.fetchone()


def mark_application_sent(draft_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE application_drafts
                SET status = 'sent',
                    decided_at = NOW(),
                    sent_at = NOW()
                WHERE id = %s
                """,
                (draft_id,),
            )
        conn.commit()


def mark_application_skipped(draft_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE application_drafts
                SET status = 'skipped',
                    decided_at = NOW()
                WHERE id = %s
                """,
                (draft_id,),
            )
        conn.commit()
