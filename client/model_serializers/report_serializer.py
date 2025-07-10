from rest_framework import serializers
from client.models import Report

# Create your serializers here.
class ReportModelSerializer(serializers.ModelSerializer):
	class Meta:
		model = Report
		fields = [
					'id',
					'location',
					'latitude',
					'longitude',
					'report_type',
					'description',
					'timestamp',
					'status',
					'sensor_data',
					'verification_status',
					'rating',
					'user',
				]
		read_only_fields = fields
