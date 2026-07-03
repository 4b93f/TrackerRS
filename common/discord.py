import requests

from config import DISCORD_WEBHOOK_URL


def send_notification(username: str, platform: str, post: dict):
    platform_colors = {"instagram": 0xE1306C, "tiktok": 0x69C9D0}

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

    embed = {
        "title": f"New post from @{username}",
        "url": url,
        "description": caption,
        "color": platform_colors.get(platform, 0x5865F2),
        "footer": {"text": f"{platform.capitalize()} · {media_type}"},
    }
    if image_url:
        embed["image"] = {"url": image_url}

    requests.post(DISCORD_WEBHOOK_URL, json={"embeds": [embed]})
    print(f"[DISCORD] Notification sent for @{username} ({platform})")
