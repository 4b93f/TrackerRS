import psycopg2
import psycopg2.extras

from config import DATABASE_URL


def _conn():
    return psycopg2.connect(DATABASE_URL)


def get_all_users() -> list[dict]:
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT user_id, username, token, last_media_id FROM users")
            return [dict(row) for row in cur.fetchall()]


def upsert_user(user_id: str, username: str, token: str, last_media_id: str | None):
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (user_id, username, token, last_media_id, updated_at)
                VALUES (%s, %s, %s, %s, NOW())
                ON CONFLICT (user_id) DO UPDATE
                SET username = EXCLUDED.username,
                    token = EXCLUDED.token,
                    last_media_id = EXCLUDED.last_media_id,
                    updated_at = NOW()
            """, (user_id, username, token, last_media_id))


def update_last_media_id(user_id: str, last_media_id: str):
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET last_media_id = %s, updated_at = NOW() WHERE user_id = %s",
                (last_media_id, user_id)
            )
