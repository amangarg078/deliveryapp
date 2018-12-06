import json
from channels import Group
from channels.auth import channel_session_user, channel_session_user_from_http
from .models import User


@channel_session_user_from_http
def ws_connect(message):
    message.reply_channel.send({"accept": True})
    user = message.user
    user.get_websocket_group.add(message.reply_channel)


@channel_session_user
def ws_disconnect(message):
    # Unsubscribe from any connected rooms
    for user_id in message.channel_session.get("id", set()):
        try:
            user = User.objects.get(pk=user_id)
            # Removes us from the room's send group. If this doesn't get run,
            # we'll get removed once our first reply message expires.
            user.websocket_group.discard(message.reply_channel)
        except User.DoesNotExist:
            pass
