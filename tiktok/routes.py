import base64
import hashlib
import secrets

from flask import Blueprint, redirect, request, session

from config import TIKTOK_CLIENT_KEY, TIKTOK_REDIRECT_URI
from tiktok.api import exchange_code, fetch_latest_video_id, fetch_username
from common.state import upsert_user

bp = Blueprint("tiktok", __name__)


def _code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


@bp.route("/tiktok/login")
def login():
    verifier = secrets.token_urlsafe(64)
    challenge = _code_challenge(verifier)
    session["tiktok_verifier"] = verifier

    auth_url = (
        "https://www.tiktok.com/v2/auth/authorize/"
        f"?client_key={TIKTOK_CLIENT_KEY}"
        f"&redirect_uri={TIKTOK_REDIRECT_URI}"
        "&scope=user.info.basic,video.list"
        "&response_type=code"
        f"&code_challenge={challenge}"
        "&code_challenge_method=S256"
    )
    return redirect(auth_url)


@bp.route("/tiktok/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return request.args.get("error_description", "Authorization failed"), 400

    verifier = session.pop("tiktok_verifier", None)
    if not verifier:
        return "Session expired, please try again", 400

    token, open_id, refresh_tok = exchange_code(code, verifier)
    if not token or not open_id:
        return "Token exchange failed", 400

    username = fetch_username(open_id, token)
    last_video_id = fetch_latest_video_id(open_id, token)

    upsert_user("tiktok", open_id, username, token, last_video_id)
    print(f"[TIKTOK] @{username} connected. Baseline video: {last_video_id}")
    return f"@{username} connected successfully. You can close this tab."
