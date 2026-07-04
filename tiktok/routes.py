import base64
import hashlib
import secrets

from flask import Blueprint, redirect, request

from config import TIKTOK_CLIENT_KEY, TIKTOK_REDIRECT_URI
from tiktok.api import exchange_code, fetch_latest_video_id, fetch_username
from common.state import upsert_user
from common.link_state import _pending as link_pending

bp = Blueprint("tiktok", __name__)

_pending: dict[str, dict] = {}  # oauth_state -> {verifier, link_state}


def _code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


@bp.route("/tiktok/login")
def login():
    verifier = secrets.token_urlsafe(64)
    challenge = _code_challenge(verifier)
    oauth_state = secrets.token_urlsafe(16)
    _pending[oauth_state] = {
        "verifier": verifier,
        "link_state": request.args.get("link_state"),
    }

    auth_url = (
        "https://www.tiktok.com/v2/auth/authorize/"
        f"?client_key={TIKTOK_CLIENT_KEY}"
        f"&redirect_uri={TIKTOK_REDIRECT_URI}"
        "&scope=user.info.basic,video.list"
        "&response_type=code"
        f"&code_challenge={challenge}"
        "&code_challenge_method=S256"
        f"&state={oauth_state}"
    )
    return redirect(auth_url)


@bp.route("/tiktok/callback")
def callback():
    code = request.args.get("code")
    oauth_state = request.args.get("state")

    if not code:
        return request.args.get("error_description", "Authorization failed"), 400

    entry = _pending.pop(oauth_state, None) if oauth_state else None
    if not entry:
        return "Session expired, please try again", 400

    verifier = entry["verifier"]
    link_info = link_pending.pop(entry["link_state"], None) if entry.get("link_state") else None
    guild_id = link_info["guild_id"] if link_info else None
    channel_id = link_info["channel_id"] if link_info else None

    token, open_id, refresh_tok = exchange_code(code, verifier)
    if not token or not open_id:
        return "Token exchange failed", 400

    username = fetch_username(open_id, token)
    last_video_id = fetch_latest_video_id(open_id, token)

    upsert_user("tiktok", open_id, username, token, last_video_id, refresh_tok, guild_id, channel_id)
    print(f"[TIKTOK] @{username} connected. Channel: {channel_id}. Baseline: {last_video_id}")
    return f"@{username} connected successfully. You can close this tab."
