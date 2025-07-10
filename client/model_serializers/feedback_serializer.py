from rest_framework import serializers
from client.models import Feedback

# Create your serializers here.
class FeedbackModelSerializer(serializers.ModelSerializer):
	class Meta:
		model = Feedback
		fields = [
					'id',
					'rating',
					'comment',
					'is_accurate',
					'timestamp',
					'parent_feedback',
					'user',
					'prediction',
					'report',
				]
		read_only_fields = fields
