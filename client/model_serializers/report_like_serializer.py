from rest_framework import serializers
from client.models import ReportLike

# Create your serializers here.
class ReportLikeModelSerializer(serializers.ModelSerializer):
	class Meta:
		model = ReportLike
		fields = [
					'id',
					'timestamp',
					'report',
					'user',
				]
		read_only_fields = fields
