from django.urls import re_path
from .consumers import GroupConsumer

websocket_urlpatterns = [
    re_path(r"ws/groups/(?P<code>[^/]+)/$", GroupConsumer.as_asgi()),
]
