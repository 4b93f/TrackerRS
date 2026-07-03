import os
import threading

from flask import Flask, redirect, request

from config import REDIRECT_URI, WEBHOOK_VERIFY_TOKEN
from instagram import exchange_code, exchange_long_lived, fetch_latest_media_id, fetch_username
from state import upsert_user
import poller

app = Flask(__name__)


# ── OAuth ──────────────────────────────────────────────────────────────────────

@app.route("/login")
def login():
    from config import INSTAGRAM_APP_ID
    auth_url = (
        "https://api.instagram.com/oauth/authorize"
        f"?client_id={INSTAGRAM_APP_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        "&scope=instagram_business_basic"
        "&response_type=code"
    )
    return redirect(auth_url)


@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return request.args.get("error_description", "Authorization failed"), 400

    token, user_id = exchange_code(code)
    if not token or not user_id:
        return "Token exchange failed", 400

    long_token = exchange_long_lived(token)
    if not long_token:
        return "Long-lived token exchange failed", 400

    username = fetch_username(user_id, long_token)
    last_media_id = fetch_latest_media_id(user_id, long_token)

    upsert_user(user_id, username, long_token, last_media_id)
    print(f"[AUTH] @{username} connected. Baseline post: {last_media_id}")
    return f"@{username} connected successfully. You can close this tab."


# ── Webhook (reserved for future use) ─────────────────────────────────────────

@app.route("/webhook", methods=["GET"])
def webhook_verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == WEBHOOK_VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403


@app.route("/webhook", methods=["POST"])
def webhook_receive():
    return "OK", 200


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    threading.Thread(target=poller.start, daemon=True).start()
    port = int(os.getenv("PORT", "8080"))
    app.run(debug=False, host="0.0.0.0", port=port)
