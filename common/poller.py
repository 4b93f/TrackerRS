import time
from typing import Callable

from config import POLL_INTERVAL
from common.discord import send_notification
from common.state import get_all_users, update_last_media_id


def start(platform: str, fetch_recent: Callable, refresh_fn: Callable | None = None):
    while True:
        time.sleep(POLL_INTERVAL)
        for user in get_all_users(platform):
            try:
                _check(platform, user, fetch_recent, refresh_fn)
            except Exception as e:
                print(f"[POLL ERROR] [{platform}] @{user['username']}: {e}")


def _check(platform: str, user: dict, fetch_recent: Callable, refresh_fn: Callable | None):
    posts = fetch_recent(user["user_id"], user["token"])

    if posts is None:
        if refresh_fn and user.get("refresh_token"):
            print(f"[TOKEN] [{platform}] @{user['username']} token expired, refreshing")
            new_token = refresh_fn(platform, user["user_id"], user["refresh_token"])
            if not new_token:
                print(f"[TOKEN] [{platform}] @{user['username']} refresh failed, re-auth needed")
                return
            posts = fetch_recent(user["user_id"], new_token)
            if not posts:
                return
        else:
            print(f"[TOKEN] [{platform}] @{user['username']} token expired, re-auth needed")
            return

    new_posts = []
    for post in posts:
        if post["id"] == user["last_media_id"]:
            break
        new_posts.append(post)

    if not new_posts:
        return

    update_last_media_id(platform, user["user_id"], posts[0]["id"])
    for post in reversed(new_posts):
        print(f"[NEW POST] [{platform}] @{user['username']}: {post.get('permalink') or post.get('share_url')}")
        send_notification(user["username"], platform, post)
