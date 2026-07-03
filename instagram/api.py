import requests

from config import INSTAGRAM_APP_ID, INSTAGRAM_APP_SECRET, INSTAGRAM_REDIRECT_URI


def exchange_code(code: str) -> tuple[str | None, str | None]:
    r = requests.post("https://api.instagram.com/oauth/access_token", data={
        "client_id": INSTAGRAM_APP_ID,
        "client_secret": INSTAGRAM_APP_SECRET,
        "grant_type": "authorization_code",
        "redirect_uri": INSTAGRAM_REDIRECT_URI,
        "code": code,
    })
    if not r.ok:
        print(f"[INSTAGRAM] Code exchange error: {r.text}")
        return None, None
    data = r.json()
    return data["access_token"], str(data["user_id"])


def exchange_long_lived(short_token: str) -> str | None:
    r = requests.get("https://graph.instagram.com/access_token", params={
        "grant_type": "ig_exchange_token",
        "client_secret": INSTAGRAM_APP_SECRET,
        "access_token": short_token,
    })
    if not r.ok:
        print(f"[INSTAGRAM] Long-lived exchange error: {r.text}")
        return None
    return r.json()["access_token"]


def fetch_username(user_id: str, token: str) -> str:
    r = requests.get(
        f"https://graph.instagram.com/{user_id}",
        params={"fields": "username", "access_token": token},
    )
    return r.json().get("username", user_id) if r.ok else user_id


def fetch_latest_media_id(user_id: str, token: str) -> str | None:
    r = requests.get(
        f"https://graph.instagram.com/{user_id}/media",
        params={"fields": "id", "limit": 1, "access_token": token},
    )
    if not r.ok:
        return None
    data = r.json().get("data", [])
    return data[0]["id"] if data else None


def fetch_recent_media(user_id: str, token: str) -> list[dict]:
    r = requests.get(
        f"https://graph.instagram.com/{user_id}/media",
        params={
            "fields": "id,caption,permalink,media_type,media_url,thumbnail_url",
            "limit": 5,
            "access_token": token,
        },
    )
    if not r.ok:
        print(f"[INSTAGRAM] Media fetch error for {user_id}: {r.text}")
        return []
    return r.json().get("data", [])
