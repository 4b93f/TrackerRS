import requests
import discord

from config import DISCORD_WEBHOOK_URL
from discord_bot.bot import send_to_channel

_COLORS = {"instagram": 0xE1306C, "tiktok": 0x69C9D0, "twitch": 0x9147FF}


def send_notification(username: str, platform: str, post: dict, channel_id: str | None = None, role_id: str | None = None):
    if platform == "twitch":
        title = f"🔴 {username} is live!"
        url = post.get("url", f"https://twitch.tv/{username}")
        description = post.get("title", "")
        if post.get("game"):
            description += f"\n**{post['game']}**"
        image_url = post.get("thumbnail_url")
        footer = "Twitch · Live"
    elif platform == "tiktok":
        title = f"New post from @{username}"
        description = post.get("title", "")
        url = post.get("share_url", "")
        image_url = post.get("cover_image_url")
        footer = "TikTok · Video"
    else:
        title = f"New post from @{username}"
        description = post.get("caption", "")
        url = post.get("permalink", "")
        image_url = post.get("media_url") or post.get("thumbnail_url")
        footer = f"Instagram · {post.get('media_type', 'POST').capitalize()}"

    if len(description) > 200:
        description = description[:200] + "..."

    embed = discord.Embed(
        title=title,
        url=url,
        description=description,
        color=_COLORS.get(platform, 0x5865F2),
    )
    embed.set_footer(text=footer)
    if image_url:
        embed.set_image(url=image_url)

    content = f"<@&{role_id}>" if role_id else None

    if channel_id:
        send_to_channel(int(channel_id), embed, content=content)
    else:
        payload = {"embeds": [embed.to_dict()]}
        if content:
            payload["content"] = content
        requests.post(DISCORD_WEBHOOK_URL, json=payload)

    print(f"[DISCORD] Notification sent for @{username} ({platform})", flush=True)
