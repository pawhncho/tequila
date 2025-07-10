import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from channels.generic.websocket import AsyncWebsocketConsumer
import json

# Create your consumers here.
class ReportConsumer(AsyncWebsocketConsumer):
	async def connect(self):
		self.group_name = 'reports'
		await self.channel_layer.group_add(self.group_name, self.channel_name)
		await self.accept()

	async def disconnect(self, close_code):
		await self.channel_layer.group_discard(self.group_name, self.channel_name)

	async def send_report(self, event):
		data = event['message']
		await self.send(text_data=json.dumps({ 'reports': data }))

class PredictionConsumer(AsyncWebsocketConsumer):
	async def connect(self):
		self.group_name = 'predictions'
		await self.channel_layer.group_add(self.group_name, self.channel_name)
		await self.accept()

	async def disconnect(self, close_code):
		await self.channel_layer.group_discard(self.group_name, self.channel_name)

	async def send_prediction(self, event):
		data = event['message']
		await self.send(text_data=json.dumps({ 'predictions': data }))

class NotificationConsumer(AsyncWebsocketConsumer):
	async def connect(self):
		self.user = self.scope['user']
		self.groups_to_join = []

		if self.user.is_authenticated:
			user_group = f"user_{self.user.id}"
			await self.channel_layer.group_add(user_group, self.channel_name)
			self.groups_to_join.append(user_group)

		global_group = 'notifications'
		await self.channel_layer.group_add(global_group, self.channel_name)
		self.groups_to_join.append(global_group)

		await self.accept()

	async def disconnect(self, close_code):
		for group in self.groups_to_join:
			await self.channel_layer.group_discard(group, self.channel_name)

	async def send_notification(self, event):
		data = event['message']
		await self.send(text_data=json.dumps({ 'notifications': data }))
