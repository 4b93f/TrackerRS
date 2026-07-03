import requests

from config import DISCORD_WEBHOOK_URL


def send_notification(post: dict, username: str):
    caption = post.get("caption", "")
    if len(caption) > 200:
        caption = caption[:200] + "..."

    image_url = post.get("media_url") or post.get("thumbnail_url")

    embed = {
        "title": f"New post from @{username}",
        "url": post.get("permalink", ""),
        "description": caption,
        "color": 0xE1306C,
        "footer": {"text": post.get("media_type", "POST").capitalize()},
    }
    if image_url:
        embed["image"] = {"url": image_url}

    requests.post(DISCORD_WEBHOOK_URL, json={"embeds": [embed]})
    print(f"[DISCORD] Notification sent for @{username}")
