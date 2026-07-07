import os
import threading

from flask import Flask, render_template

from instagram.routes import bp as instagram_bp
from instagram.api import fetch_recent_media
from tiktok.routes import bp as tiktok_bp
from twitch.routes import bp as twitch_bp
from tiktok.api import fetch_recent_videos, refresh_token as tiktok_refresh_token
from common.poller import start as start_poller
from common.state import update_token
import discord_bot.bot as bot

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))
app.register_blueprint(instagram_bp)
app.register_blueprint(tiktok_bp)
app.register_blueprint(twitch_bp)


@app.route("/tos")
def tos():
    return render_template("tos.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


def _tiktok_refresh(platform: str, user_id: str, refresh_tok: str) -> str | None:
    new_token, new_refresh = tiktok_refresh_token(refresh_tok)
    if new_token:
        update_token(platform, user_id, new_token, new_refresh)
    return new_token


if __name__ == "__main__":
    if os.getenv("DISCORD_BOT_TOKEN", "disabled") != "disabled":
        def _run_bot():
            try:
                bot.start()
            except Exception as e:
                print(f"[DISCORD BOT] Fatal error: {e}", flush=True)
        threading.Thread(target=_run_bot, daemon=True).start()

    threading.Thread(
        target=start_poller,
        args=("instagram", fetch_recent_media),
        daemon=True
    ).start()

    threading.Thread(
        target=start_poller,
        args=("tiktok", fetch_recent_videos),
        kwargs={"refresh_fn": _tiktok_refresh},
        daemon=True
    ).start()

    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
