from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Notification, Profile, Report, ReportLike, Prediction, PredictionLike, Feedback
from .model_serializers.user_serializer import UserModelSerializer
from .model_serializers.notification_serializer import NotificationModelSerializer
from .model_serializers.profile_serializer import ProfileModelSerializer
from .model_serializers.report_serializer import ReportModelSerializer
from .model_serializers.report_like_serializer import ReportLikeModelSerializer
from .model_serializers.prediction_serializer import PredictionModelSerializer
from .model_serializers.prediction_like_serializer import PredictionLikeModelSerializer
from .model_serializers.feedback_serializer import FeedbackModelSerializer

# Create your serializers here.
class UserSerializer(serializers.ModelSerializer):
	profile = ProfileModelSerializer()
	class Meta:
		model = User
		fields = ['id', 'first_name', 'last_name', 'username', 'email', 'last_login', 'date_joined', 'profile']
		read_only_fields = fields

class NotificationSerializer(serializers.ModelSerializer):
	class Meta:
		model = Notification
		fields = ['id', 'actor', 'report', 'report_like', 'prediction', 'prediction_like', 'feedback', 'action_type',
					'message', 'timestamp', 'user']
		read_only_fields = fields

class ProfileSerializer(serializers.ModelSerializer):
	user = UserModelSerializer()
	profile_picture = serializers.SerializerMethodField()

	def get_profile_picture(self, obj):
		if obj.profile_picture:
			return obj.profile_picture.url
		return None

	class Meta:
		model = Profile
		fields = ['id', 'phone_number', 'profile_picture', 'location', 'timestamp', 'last_modified',
					'verification_status', 'notification_status', 'user']
		read_only_fields = fields

class ReportSerializer(serializers.ModelSerializer):
	user = UserSerializer()
	likes = ReportLikeModelSerializer(many=True)
	class Meta:
		model = Report
		fields = ['id', 'location', 'latitude', 'longitude', 'report_type', 'description', 'timestamp', 'status',
					'sensor_data', 'verification_status', 'rating', 'user', 'likes']
		read_only_fields = fields

class ReportLikeSerializer(serializers.ModelSerializer):
	class Meta:
		model = ReportLike
		fields = ['id', 'timestamp', 'report', 'user']
		read_only_fields = fields

class PredictionSerializer(serializers.ModelSerializer):
	user = UserSerializer()
	likes = PredictionLikeModelSerializer(many=True)
	class Meta:
		model = Prediction
		fields = ['id', 'predicted_event', 'generated_text', 'confidence_score', 'valid_until', 'ai_model_version',
					'timestamp', 'user', 'report', 'likes']
		read_only_fields = fields

class PredictionLikeSerializer(serializers.ModelSerializer):
	class Meta:
		model = PredictionLike
		fields = ['id', 'timestamp', 'prediction', 'user']
		read_only_fields = fields

class FeedbackSerializer(serializers.ModelSerializer):
	class Meta:
		model = Feedback
		fields = ['id', 'rating', 'comment', 'is_accurate', 'timestamp', 'parent_feedback', 'user', 'prediction',
					'report']
		read_only_fields = fields
