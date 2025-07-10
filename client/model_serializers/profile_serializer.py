from rest_framework import serializers
from client.models import Profile

# Create your serializers here.
class ProfileModelSerializer(serializers.ModelSerializer):
	profile_picture = serializers.SerializerMethodField()

	def get_profile_picture(self, obj):
		if obj.profile_picture:
			return obj.profile_picture.url
		return None

	class Meta:
		model = Profile
		fields = [
					'id',
					'phone_number',
					'profile_picture',
					'location',
					'timestamp',
					'last_modified',
					'verification_status',
					'notification_status',
					'user',
				]
		read_only_fields = fields
