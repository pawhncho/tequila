from rest_framework import serializers
from client.models import Notification

# Create your serializers here.
class NotificationModelSerializer(serializers.ModelSerializer):
	class Meta:
		model = Notification
		fields = [
					'id',
					'actor',
					'report',
					'report_like',
					'prediction',
					'prediction_like',
					'feedback',
					'action_type',
					'message',
					'timestamp',
					'user',
				]
		read_only_fields = fields
