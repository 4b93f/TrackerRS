from flask import Blueprint, request

from twitch.api import get_stream_info, verify_signature
from twitch.state import get_channel, upsert_channel
from common.discord import send_notification

bp = Blueprint("twitch", __name__)


@bp.route("/twitch/webhook", methods=["POST"])
def webhook():
    msg_type = request.headers.get("Twitch-Eventsub-Message-Type")
    print(f"[TWITCH] Webhook received: type={msg_type}", flush=True)

    if not verify_signature(request):
        print(f"[TWITCH] Invalid signature", flush=True)
        return "Forbidden", 403

    if msg_type == "webhook_callback_verification":
        print(f"[TWITCH] Challenge verified", flush=True)
        return request.json["challenge"], 200

    if msg_type == "notification":
        event = request.json.get("event", {})
        user_id = event.get("broadcaster_user_id")
        username = event.get("broadcaster_user_name")
        print(f"[TWITCH] {username} ({user_id}) went live", flush=True)
        channel = get_channel(user_id)
        if not channel:
            print(f"[TWITCH] No channel found for {user_id}, skipping", flush=True)
        else:
            from common.state import get_role
            role_id = get_role(channel.get("guild_id"), "twitch") if channel.get("guild_id") else None
            stream = get_stream_info(user_id)
            print(f"[TWITCH] Stream info: title={stream.get('title')} game={stream.get('game_name')}", flush=True)
            post = {
                "title": stream.get("title", ""),
                "game": stream.get("game_name", ""),
                "url": f"https://twitch.tv/{event.get('broadcaster_user_login', '')}",
                "thumbnail_url": stream.get("thumbnail_url", "").replace("{width}", "1280").replace("{height}", "720"),
            }
            send_notification(username, "twitch", post, channel_id=channel.get("channel_id"), role_id=role_id)

    return "", 204
