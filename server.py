import os
import threading

from flask import Flask

from instagram.routes import bp as instagram_bp
from instagram.api import fetch_recent_media
from tiktok.routes import bp as tiktok_bp
from tiktok.api import fetch_recent_videos
from common.poller import start as start_poller

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))
app.register_blueprint(instagram_bp)
app.register_blueprint(tiktok_bp)


if __name__ == "__main__":
    threading.Thread(
        target=start_poller,
        args=("instagram", fetch_recent_media),
        daemon=True
    ).start()

    threading.Thread(
        target=start_poller,
        args=("tiktok", fetch_recent_videos),
        daemon=True
    ).start()

    port = int(os.getenv("PORT", "8080"))
    app.run(debug=True, host="0.0.0.0", port=port)
