from rest_framework import serializers
from client.models import PredictionLike

# Create your serializers here.
class PredictionLikeModelSerializer(serializers.ModelSerializer):
	class Meta:
		model = PredictionLike
		fields = [
					'id',
					'timestamp',
					'prediction',
					'user',
				]
		read_only_fields = fields
