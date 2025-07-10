from rest_framework import serializers
from django.contrib.auth.models import User

# Create your serializers here.
class UserModelSerializer(serializers.ModelSerializer):
	class Meta:
		model = User
		fields = [
					'id',
					'first_name',
					'last_name',
					'username',
					'email',
					'last_login',
					'date_joined',
				]
		read_only_fields = fields
