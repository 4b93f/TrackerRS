import psycopg2
import psycopg2.extras

from config import DATABASE_URL


def _conn():
    return psycopg2.connect(DATABASE_URL)


def get_all_users(platform: str) -> list[dict]:
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT user_id, username, token, refresh_token, last_media_id, channel_id, guild_id FROM users WHERE platform = %s",
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


def get_users_for_guild(guild_id: str) -> list[dict]:
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT platform, username FROM users WHERE guild_id = %s",
                (guild_id,)
            )
            return [dict(row) for row in cur.fetchall()]


def delete_user(platform: str, username: str, guild_id: str) -> bool:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM users WHERE platform = %s AND username = %s AND guild_id = %s",
                (platform, username, guild_id)
            )
            return cur.rowcount > 0


def set_guild_channel(guild_id: str, channel_id: str) -> int:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET channel_id = %s, updated_at = NOW() WHERE guild_id = %s",
                (channel_id, guild_id)
            )
            return cur.rowcount


def set_platform_channel(guild_id: str, platform: str, channel_id: str) -> int:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET channel_id = %s, updated_at = NOW() WHERE guild_id = %s AND platform = %s",
                (channel_id, guild_id, platform)
            )
            return cur.rowcount


def set_channel(platform: str, username: str, guild_id: str, channel_id: str) -> bool:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET guild_id = %s, channel_id = %s, updated_at = NOW() WHERE platform = %s AND username = %s",
                (guild_id, channel_id, platform, username)
            )
            return cur.rowcount > 0


def get_role(guild_id: str, platform: str) -> str | None:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT role_id FROM guild_settings WHERE guild_id = %s AND platform = %s",
                (guild_id, platform)
            )
            row = cur.fetchone()
            return row[0] if row else None


def set_role(guild_id: str, platform: str, role_id: str):
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO guild_settings (guild_id, platform, role_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (guild_id, platform) DO UPDATE SET role_id = EXCLUDED.role_id
            """, (guild_id, platform, role_id))


def update_last_media_id(platform: str, user_id: str, last_media_id: str):
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET last_media_id = %s, updated_at = NOW() WHERE platform = %s AND user_id = %s",
                (last_media_id, platform, user_id)
            )
