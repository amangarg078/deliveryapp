from channels import route
from delivery.apps.orders.consumers import ws_connect, ws_disconnect

channel_routing = [
    # route("http.request", "delivery.apps.orders.consumers.http_consumer"),
    route("websocket.connect", ws_connect),
    route("websocket.disconnect", ws_disconnect),
]