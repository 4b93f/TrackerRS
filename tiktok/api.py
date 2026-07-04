import requests

from config import TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET, TIKTOK_REDIRECT_URI


def exchange_code(code: str, code_verifier: str) -> tuple[str | None, str | None, str | None]:
    r = requests.post("https://open.tiktokapis.com/v2/oauth/token/", data={
        "client_key": TIKTOK_CLIENT_KEY,
        "client_secret": TIKTOK_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": TIKTOK_REDIRECT_URI,
        "code_verifier": code_verifier,
    }, headers={"Content-Type": "application/x-www-form-urlencoded"})
    if not r.ok:
        print(f"[TIKTOK] Code exchange error: {r.text}")
        return None, None, None
    data = r.json()
    return data.get("access_token"), data.get("open_id"), data.get("refresh_token")


def refresh_token(refresh_tok: str) -> tuple[str | None, str | None]:
    r = requests.post("https://open.tiktokapis.com/v2/oauth/token/", data={
        "client_key": TIKTOK_CLIENT_KEY,
        "client_secret": TIKTOK_CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": refresh_tok,
    }, headers={"Content-Type": "application/x-www-form-urlencoded"})
    if not r.ok:
        print(f"[TIKTOK] Refresh error: {r.text}")
        return None, None
    data = r.json()
    return data.get("access_token"), data.get("refresh_token")


def fetch_username(open_id: str, token: str) -> str:
    r = requests.get(
        "https://open.tiktokapis.com/v2/user/info/",
        params={"fields": "display_name"},
        headers={"Authorization": f"Bearer {token}"},
    )
    print(f"[TIKTOK] User info status: {r.status_code} body: {r.text}")
    if not r.ok:
        return open_id
    user = r.json().get("data", {}).get("user", {})
    return user.get("display_name") or open_id


def fetch_latest_video_id(open_id: str, token: str) -> str | None:
    videos = fetch_recent_videos(open_id, token)
    return videos[0]["id"] if videos else None


def fetch_recent_videos(open_id: str, token: str) -> list[dict] | None:
    r = requests.post(
        "https://open.tiktokapis.com/v2/video/list/",
        params={"fields": "id,create_time,share_url,cover_image_url"},
        json={"max_count": 5},
        headers={"Authorization": f"Bearer {token}"},
    )
    if r.status_code == 401:
        return None
    if not r.ok:
        print(f"[TIKTOK] Video fetch error for {open_id}: {r.text}")
        return []
    return r.json().get("data", {}).get("videos", [])
