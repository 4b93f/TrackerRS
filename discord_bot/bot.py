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
    print(f"[DISCORD BOT] Logged in as {client.user}")


@tree.command(name="link", description="Connect a social media account for tracking")
@app_commands.describe(platform="Platform to track", username="Twitch username (Twitch only)")
@app_commands.choices(platform=[
    app_commands.Choice(name="TikTok", value="tiktok"),
    app_commands.Choice(name="Instagram", value="instagram"),
    app_commands.Choice(name="Twitch", value="twitch"),
])
async def link(interaction: discord.Interaction, platform: app_commands.Choice[str], username: str | None = None):
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
    await interaction.response.send_message(
        f"Connect your **{platform.name}** account by clicking the link below.\n"
        f"Notifications will be sent to this channel.\n\n{url}\n\n"
        f"-# Link expires after use.",
        ephemeral=True,
    )


async def _send_embed(channel_id: int, embed: discord.Embed):
    channel = client.get_channel(channel_id)
    if channel:
        await channel.send(embed=embed)
    else:
        print(f"[DISCORD BOT] Channel {channel_id} not found")


def send_to_channel(channel_id: int, embed: discord.Embed):
    if not client.is_ready():
        print(f"[DISCORD BOT] Bot not ready, skipping notification")
        return
    asyncio.run_coroutine_threadsafe(_send_embed(channel_id, embed), client.loop)


def start():
    client.run(DISCORD_BOT_TOKEN, log_handler=None)
