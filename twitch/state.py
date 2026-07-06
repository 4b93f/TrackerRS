import psycopg2
import psycopg2.extras

from config import DATABASE_URL


def _conn():
    return psycopg2.connect(DATABASE_URL)


def get_channel(user_id: str) -> dict | None:
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT user_id, username, guild_id, channel_id FROM twitch_channels WHERE user_id = %s",
                (user_id,)
            )
            row = cur.fetchone()
            return dict(row) if row else None


def get_all_channels() -> list[dict]:
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT user_id, username, guild_id, channel_id FROM twitch_channels")
            return [dict(row) for row in cur.fetchall()]


def set_guild_channel(guild_id: str, channel_id: str) -> int:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE twitch_channels SET channel_id = %s WHERE guild_id = %s",
                (channel_id, guild_id)
            )
            return cur.rowcount


def get_channels_for_guild(guild_id: str) -> list[dict]:
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT user_id, username FROM twitch_channels WHERE guild_id = %s",
                (guild_id,)
            )
            return [dict(row) for row in cur.fetchall()]


def delete_channel(user_id: str):
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM twitch_channels WHERE user_id = %s", (user_id,))


def upsert_channel(user_id: str, username: str, guild_id: str | None, channel_id: str | None):
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO twitch_channels (user_id, username, guild_id, channel_id)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE
                SET username = EXCLUDED.username,
                    guild_id = COALESCE(EXCLUDED.guild_id, twitch_channels.guild_id),
                    channel_id = COALESCE(EXCLUDED.channel_id, twitch_channels.channel_id)
            """, (user_id, username, guild_id, channel_id))
