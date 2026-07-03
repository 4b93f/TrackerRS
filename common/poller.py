import time
from typing import Callable

from config import POLL_INTERVAL
from common.discord import send_notification
from common.state import get_all_users, update_last_media_id


def start(platform: str, fetch_recent: Callable[[str, str], list[dict]]):
    while True:
        time.sleep(POLL_INTERVAL)
        for user in get_all_users(platform):
            try:
                _check(platform, user, fetch_recent)
            except Exception as e:
                print(f"[POLL ERROR] [{platform}] @{user['username']}: {e}")


def _check(platform: str, user: dict, fetch_recent: Callable[[str, str], list[dict]]):
    posts = fetch_recent(user["user_id"], user["token"])
    new_posts = []
    for post in posts:
        if post["id"] == user["last_media_id"]:
            break
        new_posts.append(post)

    if not new_posts:
        return

    update_last_media_id(platform, user["user_id"], posts[0]["id"])
    for post in reversed(new_posts):
        print(f"[NEW POST] [{platform}] @{user['username']}: {post.get('permalink')}")
        send_notification(user["username"], platform, post)
