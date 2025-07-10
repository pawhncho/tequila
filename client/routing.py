from django.urls import path, re_path
from . import consumers

# Create your routing here.
websocket_urlpatterns = [
	re_path(r'ws/reports/$', consumers.ReportConsumer.as_asgi()),
	re_path(r'ws/predictions/$', consumers.PredictionConsumer.as_asgi()),
	re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
]
