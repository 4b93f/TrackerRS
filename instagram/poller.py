import time

from config import POLL_INTERVAL
from discord import send_notification
from instagram import fetch_recent_media
from state import get_all_users, update_last_media_id


def start():
    while True:
        time.sleep(POLL_INTERVAL)
        for user in get_all_users():
            try:
                _check(user)
            except Exception as e:
                print(f"[POLL ERROR] @{user['username']}: {e}")


def _check(user: dict):
    posts = fetch_recent_media(user["user_id"], user["token"])
    new_posts = []
    for post in posts:
        if post["id"] == user["last_media_id"]:
            break
        new_posts.append(post)

    if not new_posts:
        return

    update_last_media_id(user["user_id"], posts[0]["id"])
    for post in reversed(new_posts):
        print(f"[NEW POST] @{user['username']}: {post.get('permalink')}")
        send_notification(post, user["username"])
