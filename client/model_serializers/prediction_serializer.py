from rest_framework import serializers
from client.models import Prediction

# Create your serializers here.
class PredictionModelSerializer(serializers.ModelSerializer):
	class Meta:
		model = Prediction
		fields = [
					'id',
					'predicted_event',
					'generated_text',
					'confidence_score',
					'valid_until',
					'ai_model_version',
					'timestamp',
					'user',
					'report',
				]
		read_only_fields = fields
