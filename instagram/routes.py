import secrets

from flask import Blueprint, redirect, request

from config import INSTAGRAM_APP_ID, INSTAGRAM_REDIRECT_URI, WEBHOOK_VERIFY_TOKEN
from instagram.api import exchange_code, exchange_long_lived, fetch_latest_media_id, fetch_username
from common.state import upsert_user
from common.link_state import _pending as link_pending

bp = Blueprint("instagram", __name__)

_pending: dict[str, str] = {}  # oauth_state -> link_state


@bp.route("/instagram/login")
def login():
    oauth_state = secrets.token_urlsafe(16)
    _pending[oauth_state] = request.args.get("link_state")

    auth_url = (
        "https://api.instagram.com/oauth/authorize"
        f"?client_id={INSTAGRAM_APP_ID}"
        f"&redirect_uri={INSTAGRAM_REDIRECT_URI}"
        "&scope=instagram_business_basic"
        "&response_type=code"
        f"&state={oauth_state}"
    )
    return redirect(auth_url)


@bp.route("/instagram/callback")
def callback():
    code = request.args.get("code")
    oauth_state = request.args.get("state")

    if not code:
        return request.args.get("error_description", "Authorization failed"), 400

    link_state = _pending.pop(oauth_state, None) if oauth_state else None
    link_info = link_pending.pop(link_state, None) if link_state else None
    guild_id = link_info["guild_id"] if link_info else None
    channel_id = link_info["channel_id"] if link_info else None

    token, user_id = exchange_code(code)
    if not token or not user_id:
        return "Token exchange failed", 400

    long_token = exchange_long_lived(token)
    if not long_token:
        return "Long-lived token exchange failed", 400

    username = fetch_username(user_id, long_token)
    last_media_id = fetch_latest_media_id(user_id, long_token)

    upsert_user("instagram", user_id, username, long_token, last_media_id, None, guild_id, channel_id)
    print(f"[INSTAGRAM] @{username} connected. Channel: {channel_id}. Baseline: {last_media_id}")
    return f"@{username} connected successfully. You can close this tab."


@bp.route("/instagram/webhook", methods=["GET"])
def webhook_verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == WEBHOOK_VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403


@bp.route("/instagram/webhook", methods=["POST"])
def webhook_receive():
    return "OK", 200
