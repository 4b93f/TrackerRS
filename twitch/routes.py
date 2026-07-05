from flask import Blueprint, request

from twitch.api import get_stream_info, verify_signature
from twitch.state import get_channel, upsert_channel
from common.discord import send_notification

bp = Blueprint("twitch", __name__)


@bp.route("/twitch/webhook", methods=["POST"])
def webhook():
    if not verify_signature(request):
        return "Forbidden", 403

    msg_type = request.headers.get("Twitch-Eventsub-Message-Type")

    if msg_type == "webhook_callback_verification":
        return request.json["challenge"], 200

    if msg_type == "notification":
        event = request.json.get("event", {})
        user_id = event.get("broadcaster_user_id")
        username = event.get("broadcaster_user_name")
        channel = get_channel(user_id)
        if channel:
            stream = get_stream_info(user_id)
            post = {
                "title": stream.get("title", ""),
                "game": stream.get("game_name", ""),
                "url": f"https://twitch.tv/{event.get('broadcaster_user_login', '')}",
                "thumbnail_url": stream.get("thumbnail_url", "").replace("{width}", "1280").replace("{height}", "720"),
            }
            print(f"[TWITCH] {username} went live")
            send_notification(username, "twitch", post, channel_id=channel.get("channel_id"))

    return "", 204
