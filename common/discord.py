import requests
import discord

from config import DISCORD_WEBHOOK_URL
from discord_bot.bot import send_to_channel

_COLORS = {"instagram": 0xE1306C, "tiktok": 0x69C9D0}


def send_notification(username: str, platform: str, post: dict, channel_id: str | None = None):
    if platform == "tiktok":
        caption = post.get("title", "")
        url = post.get("share_url", "")
        image_url = post.get("cover_image_url")
        media_type = "Video"
    else:
        caption = post.get("caption", "")
        url = post.get("permalink", "")
        image_url = post.get("media_url") or post.get("thumbnail_url")
        media_type = post.get("media_type", "POST").capitalize()

    if len(caption) > 200:
        caption = caption[:200] + "..."

    embed = discord.Embed(
        title=f"New post from @{username}",
        url=url,
        description=caption,
        color=_COLORS.get(platform, 0x5865F2),
    )
    embed.set_footer(text=f"{platform.capitalize()} · {media_type}")
    if image_url:
        embed.set_image(url=image_url)

    if channel_id:
        send_to_channel(int(channel_id), embed)
    else:
        requests.post(DISCORD_WEBHOOK_URL, json={"embeds": [embed.to_dict()]})

    print(f"[DISCORD] Notification sent for @{username} ({platform})")
