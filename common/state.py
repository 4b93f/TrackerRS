import psycopg2
import psycopg2.extras

from config import DATABASE_URL


def _conn():
    return psycopg2.connect(DATABASE_URL)


def get_all_users(platform: str) -> list[dict]:
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT user_id, username, token, refresh_token, last_media_id, channel_id FROM users WHERE platform = %s",
                (platform,)
            )
            return [dict(row) for row in cur.fetchall()]


def upsert_user(
    platform: str,
    user_id: str,
    username: str,
    token: str,
    last_media_id: str | None,
    refresh_token: str | None = None,
    guild_id: str | None = None,
    channel_id: str | None = None,
):
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (platform, user_id, username, token, refresh_token, last_media_id, guild_id, channel_id, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (platform, user_id) DO UPDATE
                SET username = EXCLUDED.username,
                    token = EXCLUDED.token,
                    refresh_token = EXCLUDED.refresh_token,
                    last_media_id = EXCLUDED.last_media_id,
                    guild_id = COALESCE(EXCLUDED.guild_id, users.guild_id),
                    channel_id = COALESCE(EXCLUDED.channel_id, users.channel_id),
                    updated_at = NOW()
            """, (platform, user_id, username, token, refresh_token, last_media_id, guild_id, channel_id))


def update_token(platform: str, user_id: str, token: str, refresh_token: str | None):
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET token = %s, refresh_token = %s, updated_at = NOW() WHERE platform = %s AND user_id = %s",
                (token, refresh_token, platform, user_id)
            )


def update_last_media_id(platform: str, user_id: str, last_media_id: str):
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET last_media_id = %s, updated_at = NOW() WHERE platform = %s AND user_id = %s",
                (last_media_id, platform, user_id)
            )
