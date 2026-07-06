import asyncio
import secrets

import discord
from discord import app_commands

from config import DISCORD_BOT_TOKEN, BASE_URL
from common.link_state import _pending as link_pending

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@client.event
async def on_ready():
    await tree.sync()
    print(f"[DISCORD BOT] Logged in as {client.user}", flush=True)


@tree.command(name="link", description="Connect a TikTok or Instagram account for tracking")
@app_commands.describe(platform="Platform to track")
@app_commands.choices(platform=[
    app_commands.Choice(name="TikTok", value="tiktok"),
    app_commands.Choice(name="Instagram", value="instagram"),
])
async def link(interaction: discord.Interaction, platform: app_commands.Choice[str]):
    print(f"[DISCORD BOT] /link {platform.value} by {interaction.user} in guild {interaction.guild_id}", flush=True)
    state = secrets.token_urlsafe(16)
    link_pending[state] = {
        "guild_id": str(interaction.guild_id),
        "channel_id": str(interaction.channel_id),
    }
    url = f"{BASE_URL}/{platform.value}/login?link_state={state}"
    print(f"[DISCORD BOT] {platform.value} link generated for guild {interaction.guild_id}", flush=True)
    await interaction.response.send_message(
        f"Connect your **{platform.name}** account by clicking the link below.\n"
        f"Notifications will be sent to this channel.\n\n{url}\n\n"
        f"-# Link expires after use.",
        ephemeral=True,
    )


@tree.command(name="track", description="Track a Twitch channel for live notifications")
@app_commands.describe(username="Twitch channel name")
async def track(interaction: discord.Interaction, username: str):
    print(f"[DISCORD BOT] /track {username} by {interaction.user} in guild {interaction.guild_id}", flush=True)
    await interaction.response.defer(ephemeral=True)
    from twitch.api import get_user, subscribe
    from twitch.state import upsert_channel
    user_id, display_name = await asyncio.to_thread(get_user, username)
    if not user_id:
        await interaction.followup.send(f"Twitch user `{username}` not found.", ephemeral=True)
        return
    ok = await asyncio.to_thread(subscribe, user_id)
    if not ok:
        await interaction.followup.send("Failed to subscribe. Check server logs.", ephemeral=True)
        return
    await asyncio.to_thread(
        upsert_channel, user_id, display_name,
        str(interaction.guild_id), str(interaction.channel_id)
    )
    print(f"[DISCORD BOT] Twitch @{display_name} linked to channel {interaction.channel_id}", flush=True)
    await interaction.followup.send(
        f"Now tracking **{display_name}** on Twitch. Notifications will be sent to this channel.",
        ephemeral=True,
    )


@tree.command(name="list", description="List tracked accounts for this server")
@app_commands.describe(platform="Filter by platform (optional)")
@app_commands.choices(platform=[
    app_commands.Choice(name="TikTok", value="tiktok"),
    app_commands.Choice(name="Instagram", value="instagram"),
    app_commands.Choice(name="Twitch", value="twitch"),
])
async def list_accounts(interaction: discord.Interaction, platform: app_commands.Choice[str] | None = None):
    try:
        from common.state import get_users_for_guild
        from twitch.state import get_channels_for_guild
        guild_id = str(interaction.guild_id)
        lines = []
        if platform is None or platform.value != "twitch":
            users = await asyncio.to_thread(get_users_for_guild, guild_id)
            lines += [f"**{u['platform'].capitalize()}** — @{u['username']}" for u in users
                      if platform is None or u['platform'] == platform.value]
        if platform is None or platform.value == "twitch":
            twitch = await asyncio.to_thread(get_channels_for_guild, guild_id)
            lines += [f"**Twitch** — {t['username']}" for t in twitch]
        if not lines:
            await interaction.response.send_message("No tracked accounts.", ephemeral=True)
        else:
            await interaction.response.send_message("\n".join(lines), ephemeral=True)
    except Exception as e:
        print(f"[DISCORD BOT] /list error: {e}", flush=True)
        await interaction.response.send_message(f"Error: {e}", ephemeral=True)


@tree.command(name="unlink", description="Stop tracking an account")
@app_commands.describe(platform="Platform", username="Username to untrack")
@app_commands.choices(platform=[
    app_commands.Choice(name="TikTok", value="tiktok"),
    app_commands.Choice(name="Instagram", value="instagram"),
    app_commands.Choice(name="Twitch", value="twitch"),
])
async def unlink(interaction: discord.Interaction, platform: app_commands.Choice[str], username: str):
    print(f"[DISCORD BOT] /unlink {platform.value} {username} by {interaction.user}", flush=True)
    guild_id = str(interaction.guild_id)
    if platform.value == "twitch":
        from twitch.api import get_user, unsubscribe
        from twitch.state import delete_channel
        user_id, _ = await asyncio.to_thread(get_user, username)
        if not user_id:
            await interaction.response.send_message(f"Twitch user `{username}` not found.", ephemeral=True)
            return
        await asyncio.to_thread(unsubscribe, user_id)
        await asyncio.to_thread(delete_channel, user_id)
    else:
        from common.state import delete_user
        deleted = await asyncio.to_thread(delete_user, platform.value, username, guild_id)
        if not deleted:
            await interaction.response.send_message(f"`{username}` not found in tracked {platform.name} accounts.", ephemeral=True)
            return
    await interaction.response.send_message(f"Stopped tracking **@{username}** on {platform.name}.", ephemeral=True)


@tree.command(name="setrole", description="Set a role to ping for a platform's notifications")
@app_commands.describe(platform="Platform", role="Role to ping")
@app_commands.choices(platform=[
    app_commands.Choice(name="TikTok", value="tiktok"),
    app_commands.Choice(name="Instagram", value="instagram"),
    app_commands.Choice(name="Twitch", value="twitch"),
])
async def setrole(interaction: discord.Interaction, platform: app_commands.Choice[str], role: discord.Role):
    try:
        from common.state import set_role
        await asyncio.to_thread(set_role, str(interaction.guild_id), platform.value, str(role.id))
        print(f"[DISCORD BOT] Role {role.id} set for {platform.value} in guild {interaction.guild_id}", flush=True)
        await interaction.response.send_message(
            f"{platform.name} notifications will now ping **@{role.name}**.", ephemeral=True
        )
    except Exception as e:
        print(f"[DISCORD BOT] /setrole error: {e}", flush=True)
        await interaction.response.send_message(f"Error: {e}", ephemeral=True)


@tree.command(name="setchannel", description="Send all notifications for this server to this channel")
async def setchannel(interaction: discord.Interaction):
    channel_id = str(interaction.channel_id)
    guild_id = str(interaction.guild_id)
    print(f"[DISCORD BOT] /setchannel guild {guild_id} -> channel {channel_id}", flush=True)

    from common.state import set_guild_channel
    from twitch.state import set_guild_channel as twitch_set_guild_channel
    count = await asyncio.to_thread(set_guild_channel, guild_id, channel_id)
    count += await asyncio.to_thread(twitch_set_guild_channel, guild_id, channel_id)
    await interaction.response.send_message(
        f"Done. {count} tracked account(s) will now send notifications to this channel.",
        ephemeral=True,
    )


@tree.command(name="test", description="Send a test notification to this channel")
@app_commands.describe(platform="Platform to simulate")
@app_commands.choices(platform=[
    app_commands.Choice(name="TikTok", value="tiktok"),
    app_commands.Choice(name="Instagram", value="instagram"),
    app_commands.Choice(name="Twitch", value="twitch"),
])
async def test(interaction: discord.Interaction, platform: app_commands.Choice[str]):
    try:
        fake_posts = {
            "tiktok": {"title": "Test TikTok post", "share_url": "https://tiktok.com", "cover_image_url": None},
            "instagram": {"caption": "Test Instagram post", "permalink": "https://instagram.com", "media_type": "IMAGE", "media_url": None},
            "twitch": {"title": "Test stream title", "game": "Just Chatting", "url": "https://twitch.tv/test", "thumbnail_url": None},
        }
        embed = discord.Embed(title=f"Test {platform.name} notification", description="If you see this, notifications are working.", color=0x00FF00)
        await interaction.channel.send(embed=embed)
        await interaction.response.send_message(f"Test sent.", ephemeral=True)
    except Exception as e:
        print(f"[DISCORD BOT] /test error: {e}", flush=True)
        await interaction.response.send_message(f"Error: {e}", ephemeral=True)


async def _send_embed(channel_id: int, embed: discord.Embed, content: str | None = None):
    channel = client.get_channel(channel_id)
    if channel:
        await channel.send(content=content, embed=embed)
        print(f"[DISCORD BOT] Embed sent to channel {channel_id}", flush=True)
    else:
        print(f"[DISCORD BOT] Channel {channel_id} not found", flush=True)


def send_to_channel(channel_id: int, embed: discord.Embed, content: str | None = None):
    if not client.is_ready():
        print(f"[DISCORD BOT] Bot not ready, skipping notification to {channel_id}", flush=True)
        return
    asyncio.run_coroutine_threadsafe(_send_embed(channel_id, embed, content), client.loop)


def start():
    client.run(DISCORD_BOT_TOKEN, log_handler=None)
