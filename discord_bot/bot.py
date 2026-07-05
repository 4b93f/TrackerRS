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


@tree.command(name="link", description="Connect a social media account for tracking")
@app_commands.describe(platform="Platform to track", username="Twitch username (Twitch only)")
@app_commands.choices(platform=[
    app_commands.Choice(name="TikTok", value="tiktok"),
    app_commands.Choice(name="Instagram", value="instagram"),
    app_commands.Choice(name="Twitch", value="twitch"),
])
async def link(interaction: discord.Interaction, platform: app_commands.Choice[str], username: str | None = None):
    print(f"[DISCORD BOT] /link {platform.value} by {interaction.user} in guild {interaction.guild_id}", flush=True)
    if platform.value == "twitch":
        if not username:
            await interaction.response.send_message("Provide a Twitch username: `/link twitch username:streamername`", ephemeral=True)
            return
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
        return

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


@tree.command(name="setchannel", description="Move notifications for a tracked account to this channel")
@app_commands.describe(platform="Platform", username="Username or Twitch channel name")
@app_commands.choices(platform=[
    app_commands.Choice(name="TikTok", value="tiktok"),
    app_commands.Choice(name="Instagram", value="instagram"),
    app_commands.Choice(name="Twitch", value="twitch"),
])
async def setchannel(interaction: discord.Interaction, platform: app_commands.Choice[str], username: str):
    print(f"[DISCORD BOT] /setchannel {platform.value} {username} -> channel {interaction.channel_id}", flush=True)
    channel_id = str(interaction.channel_id)
    guild_id = str(interaction.guild_id)

    if platform.value == "twitch":
        from twitch.api import get_user
        from twitch.state import upsert_channel
        user_id, display_name = await asyncio.to_thread(get_user, username)
        if not user_id:
            await interaction.response.send_message(f"Twitch user `{username}` not found.", ephemeral=True)
            return
        await asyncio.to_thread(upsert_channel, user_id, display_name, guild_id, channel_id)
        await interaction.response.send_message(
            f"**{display_name}** Twitch notifications moved to this channel.", ephemeral=True
        )
    else:
        from common.state import set_channel
        updated = await asyncio.to_thread(set_channel, platform.value, username, guild_id, channel_id)
        if not updated:
            await interaction.response.send_message(
                f"`{username}` not found in tracked {platform.name} accounts.", ephemeral=True
            )
            return
        await interaction.response.send_message(
            f"**@{username}** {platform.name} notifications moved to this channel.", ephemeral=True
        )


@tree.command(name="test", description="Send a test notification to this channel")
@app_commands.describe(platform="Platform to simulate")
@app_commands.choices(platform=[
    app_commands.Choice(name="TikTok", value="tiktok"),
    app_commands.Choice(name="Instagram", value="instagram"),
    app_commands.Choice(name="Twitch", value="twitch"),
])
async def test(interaction: discord.Interaction, platform: app_commands.Choice[str]):
    from common.discord import send_notification
    fake_posts = {
        "tiktok": {"title": "Test TikTok post", "share_url": "https://tiktok.com", "cover_image_url": None},
        "instagram": {"caption": "Test Instagram post", "permalink": "https://instagram.com", "media_type": "IMAGE", "media_url": None},
        "twitch": {"title": "Test stream title", "game": "Just Chatting", "url": "https://twitch.tv/test", "thumbnail_url": None},
    }
    send_notification("testuser", platform.value, fake_posts[platform.value], channel_id=str(interaction.channel_id))
    await interaction.response.send_message(f"Test {platform.name} notification sent.", ephemeral=True)


async def _send_embed(channel_id: int, embed: discord.Embed):
    channel = client.get_channel(channel_id)
    if channel:
        await channel.send(embed=embed)
        print(f"[DISCORD BOT] Embed sent to channel {channel_id}", flush=True)
    else:
        print(f"[DISCORD BOT] Channel {channel_id} not found", flush=True)


def send_to_channel(channel_id: int, embed: discord.Embed):
    if not client.is_ready():
        print(f"[DISCORD BOT] Bot not ready, skipping notification to {channel_id}", flush=True)
        return
    asyncio.run_coroutine_threadsafe(_send_embed(channel_id, embed), client.loop)


def start():
    client.run(DISCORD_BOT_TOKEN, log_handler=None)
