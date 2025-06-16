from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/symptoms/chat/$', consumers.ChatConsumer.as_asgi()),  # 症狀頁面也使用同一個消費者
] 