import hashlib
import hmac

import requests

from config import TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET, TWITCH_WEBHOOK_SECRET, BASE_URL

_app_token: str | None = None


def _get_app_token() -> str:
    global _app_token
    if _app_token:
        return _app_token
    r = requests.post("https://id.twitch.tv/oauth2/token", data={
        "client_id": TWITCH_CLIENT_ID,
        "client_secret": TWITCH_CLIENT_SECRET,
        "grant_type": "client_credentials",
    })
    _app_token = r.json()["access_token"]
    return _app_token


def _headers() -> dict:
    return {
        "Client-Id": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {_get_app_token()}",
    }


def get_user(username: str) -> tuple[str | None, str | None]:
    r = requests.get(
        "https://api.twitch.tv/helix/users",
        params={"login": username},
        headers=_headers(),
    )
    data = r.json().get("data", [])
    if not data:
        return None, None
    return data[0]["id"], data[0]["display_name"]


def get_stream_info(user_id: str) -> dict:
    r = requests.get(
        "https://api.twitch.tv/helix/streams",
        params={"user_id": user_id},
        headers=_headers(),
    )
    data = r.json().get("data", [])
    return data[0] if data else {}


def subscribe(user_id: str) -> bool:
    r = requests.post(
        "https://api.twitch.tv/helix/eventsub/subscriptions",
        json={
            "type": "stream.online",
            "version": "1",
            "condition": {"broadcaster_user_id": user_id},
            "transport": {
                "method": "webhook",
                "callback": f"{BASE_URL}/twitch/webhook",
                "secret": TWITCH_WEBHOOK_SECRET,
            },
        },
        headers={**_headers(), "Content-Type": "application/json"},
    )
    print(f"[TWITCH] Subscribe {user_id}: {r.status_code} {r.text}")
    return r.status_code in (200, 202, 409)


def verify_signature(request) -> bool:
    msg_id = request.headers.get("Twitch-Eventsub-Message-Id", "")
    timestamp = request.headers.get("Twitch-Eventsub-Message-Timestamp", "")
    body = request.get_data(as_text=True)
    message = msg_id + timestamp + body
    expected = "sha256=" + hmac.new(
        TWITCH_WEBHOOK_SECRET.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()
    sig = request.headers.get("Twitch-Eventsub-Message-Signature", "")
    return hmac.compare_digest(expected, sig)
