from django.shortcuts import render
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core import signing
from django.core.mail import send_mail
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification, Profile, Report, ReportLike, Prediction, PredictionLike, Feedback
from .serializers import (
	UserSerializer,
	NotificationSerializer,
	ProfileSerializer,
	ReportSerializer,
	ReportLikeSerializer,
	PredictionSerializer,
	PredictionLikeSerializer,
	FeedbackSerializer
)
from transformers import pipeline

model_name = 'distilbert-base-uncased-finetuned-sst-2-english'

sentiment_analysis_model = pipeline('sentiment-analysis', model=model_name, device=-1)

# Create your views here.
def analysis(reports):
	positive = 0
	negative = 0
	for report in reports:
		analysis_description = sentiment_analysis_model(report.description)[0]
		if analysis_description['label'] == 'POSITIVE':
			positive += 1
		elif analysis_description['label'] == 'NEGATIVE':
			negative += 1
	if positive > negative:
		return 'POSITIVE'
	elif negative > positive:
		return 'NEGATIVE'
	else:
		return 'NEUTRAL'

def reset_password_page(request):
	return render(request, 'client/reset-password.html')

@api_view(['GET'])
def register_admin(request):
	if User.objects.filter(username='admin').exists():
		return Response({ 'data': 'Admin user already exists', 'status': False })
	User.objects.create_superuser(username='admin', password='admin')
	return Response({ 'data': 'Created admin user', 'status': True })

@api_view(['POST'])
def login(request):
	username = request.data.get('username')
	password = request.data.get('password')
	if not username or not password:
		return Response({ 'data': 'Fields are required', 'status': False })
	user = authenticate(username=username, password=password)
	if user:
		token = Token.objects.filter(user=user).first()
		if token:
			return Response({ 'data': token.key, 'status': True })
		return Response({ 'data': 'Token generation failed', 'status': False })
	return Response({ 'data': 'Invalid credentials', 'status': False })

@api_view(['POST'])
def register(request):
	username = request.data.get('username')
	email = request.data.get('email')
	password = request.data.get('password')
	if not username or not email or not password:
		return Response({ 'data': 'Fields are required', 'status': False })
	if User.objects.filter(username=username).exists():
		return Response({ 'data': 'Username already exists', 'status': False })
	if User.objects.filter(email=email).exists():
		return Response({ 'data': 'Email already exists', 'status': False })
	user = User.objects.create_user(username=username, email=email, password=password)
	Profile.objects.create(user=user)
	token = Token.objects.create(user=user)
	return Response({ 'data': token.key, 'status': True })

@api_view(['POST'])
def forgot_password(request):
	email = request.data.get('email')
	if not email:
		return Response({ 'data': 'Fields are required', 'status': False })
	if not User.objects.filter(email=email).exists():
		return Response({ 'data': 'Invalid email address', 'status': False })
	user = User.objects.filter(email=email).first()
	token = signing.dumps({ 'identification': user.id })
	send_mail(
		'Reset Password',
		f'Reset your password: {request.get_host()}/api/reset-password/?token={token}',
		'Future Pulse',
		[user.email]
	)
	return Response({ 'data': 'Email has been sent', 'status': True })

@api_view(['POST'])
def reset_password(request, token):
	try:
		token = signing.loads(token, max_age=3600)
	except:
		return Response({ 'data': 'Invalid token', 'status': False })
	if not User.objects.filter(id=token['identification']).exists():
		return Response({ 'data': 'User not found', 'status': False })
	new_password = request.data.get('new-password')
	if not new_password:
		return Response({ 'data': 'Fields are required', 'status': False })
	user = User.objects.filter(id=token['identification']).first()
	user.set_password(new_password)
	user.save()
	return Response({ 'data': 'Password has been changed', 'status': True })

@api_view(['GET'])
def send_verification_email(request):
	token = request.GET.get('token')
	if not token:
		return Response({ 'data': 'Invalid parameters', 'status': False })
	if not Token.objects.filter(key=token).exists():
		return Response({ 'data': 'Invalid token', 'status': False })
	token = Token.objects.filter(key=token).first()
	user = token.user
	token = signing.dumps({ 'identification': user.id })
	send_mail(
		'Email Verification',
		f'Verify your email address: {request.get_host()}/api/verify-email/{token}/',
		'Future Pulse',
		[user.email]
	)
	return Response({ 'data': 'Email has been sent', 'status': True })

@api_view(['GET'])
def verify_email(request, token):
	try:
		token = signing.loads(token, max_age=3600)
	except:
		return Response({ 'data': 'Invalid token', 'status': False })
	if not User.objects.filter(id=token['identification']).exists():
		return Response({ 'data': 'User not found', 'status': False })
	user = User.objects.filter(id=token['identification']).first()
	profile = Profile.objects.filter(user=user).first()
	profile.verification_status = True
	profile.save()
	return Response({ 'data': 'Your account has been verified', 'status': True })

@api_view(['GET'])
def profile(request):
	token = request.GET.get('token')
	if not token:
		return Response({ 'data': 'Invalid parameters', 'status': False })
	if not Token.objects.filter(key=token).exists():
		return Response({ 'data': 'Invalid token', 'status': False })
	token = Token.objects.filter(key=token).first()
	user = token.user
	profile = Profile.objects.filter(user=user).first()
	profile_serializer = ProfileSerializer(profile)
	return Response({ 'data': profile_serializer.data, 'status': True })

@api_view(['GET'])
def notifications(request):
	token = request.GET.get('token')
	if not token:
		return Response({ 'data': 'Invalid parameters', 'status': False })
	if not Token.objects.filter(key=token).exists():
		return Response({ 'data': 'Invalid token', 'status': False })
	token = Token.objects.filter(key=token).first()
	user = token.user
	notifications = Notification.objects.filter(user=user).all()
	notifications_serializer = NotificationSerializer(notifications, many=True)
	return Response({ 'data': notifications_serializer.data, 'status': True })

@api_view(['GET'])
def turn_on_notifications(request):
	token = request.GET.get('token')
	if not token:
		return Response({ 'data': 'Invalid parameters', 'status': False })
	if not Token.objects.filter(key=token).exists():
		return Response({ 'data': 'Invalid token', 'status': False })
	token = Token.objects.filter(key=token).first()
	user = token.user
	profile = Profile.objects.filter(user=user).first()
	profile.notification_status = True
	profile.save()
	return Response({ 'data': 'Notification is on', 'status': True })

@api_view(['GET'])
def turn_off_notifications(request):
	token = request.GET.get('token')
	if not token:
		return Response({ 'data': 'Invalid parameters', 'status': False })
	if not Token.objects.filter(key=token).exists():
		return Response({ 'data': 'Invalid token', 'status': False })
	token = Token.objects.filter(key=token).first()
	user = token.user
	profile = Profile.objects.filter(user=user).first()
	profile.notification_status = False
	profile.save()
	return Response({ 'data': 'Notification is off', 'status': True })

@api_view(['POST'])
def update_profile(request):
	token = request.GET.get('token')
	if not token:
		return Response({ 'data': 'Invalid parameters', 'status': False })
	if not Token.objects.filter(key=token).exists():
		return Response({ 'data': 'Invalid token', 'status': False })
	token = Token.objects.filter(key=token).first()
	user = token.user
	profile = Profile.objects.filter(user=user).first()
	if request.data.get('first-name'):
		user.first_name = request.data.get('first-name')
	if request.data.get('last-name'):
		user.last_name = request.data.get('last-name')
	if request.data.get('email'):
		if User.objects.filter(email=request.data.get('email')).exists():
			return Response({ 'data': 'Email already exists', 'status': False })
		user.email = request.data.get('email')
		profile.verification_status = False
	if request.data.get('username'):
		if User.objects.filter(username=request.data.get('username')).exists():
			return Response({ 'data': 'Username already exists', 'status': False })
	if request.data.get('profile-picture'):
		profile.profile_picture = request.FILES.get('profile-picture')
	if request.data.get('phone-number'):
		profile.phone_number = request.data.get('phone-number')
	if request.data.get('location'):
		profile.location = request.data.get('location')
	profile.last_modified = timezone.now()
	user.save()
	profile.save()
	return Response({ 'data': 'Profile has been updated', 'status': True })

@api_view(['POST'])
def submit_report(request):
	token = request.GET.get('token')
	if not token:
		return Response({ 'data': 'Invalid parameters', 'status': False })
	if not Token.objects.filter(key=token).exists():
		return Response({ 'data': 'Invalid token', 'status': False })
	token = Token.objects.filter(key=token).first()
	user = token.user
	location = request.data.get('location')
	latitude = request.data.get('latitude')
	longitude = request.data.get('longitude')
	report_type = request.data.get('report-type')
	description = request.data.get('description')
	sensor = request.data.get('sensor-data')
	rating = request.data.get('rating')
	if not location or not latitude or not longitude or not report_type or not description or not sensor or not rating:
		return Response({ 'data': 'Fields are required', 'status': False })
	report = Report.objects.create(
		location=location,
		latitude=latitude,
		longitude=longitude,
		report_type=report_type,
		description=description,
		sensor_data=sensor,
		status='active',
		rating=rating,
		user=user
	)
	now = timezone.now()
	last_24_hours = timezone.now() - timedelta(hours=24)
	reports = Report.objects.filter(timestamp__gte=last_24_hours, timestamp__lte=now).all()[::-1]
	reports_serializer = ReportSerializer(reports, many=True)
	channel_layer = get_channel_layer()
	async_to_sync(channel_layer.group_send)(
		'reports',
		{
			'type': 'send_report',
			'message': reports_serializer.data,
		}
	)
	async_to_sync(channel_layer.group_send)(
		'notifications',
		{
			'type': 'send_notification',
			'message': {
				'data': f'{report.user} reported {report.description} at {report.location}',
			},
		}
	)
	return Response({ 'data': 'Report has been submitted', 'status': True })

@api_view(['GET'])
def reports(request):
	token = request.GET.get('token')
	if not token:
		return Response({ 'data': 'Invalid parameters', 'status': False })
	if not Token.objects.filter(key=token).exists():
		return Response({ 'data': 'Invalid token', 'status': False })
	now = timezone.now()
	last_24_hours = timezone.now() - timedelta(hours=24)
	reports = Report.objects.filter(timestamp__gte=last_24_hours, timestamp__lte=now).all()[::-1]
	reports_serializer = ReportSerializer(reports, many=True)
	return Response({ 'data': reports_serializer.data, 'status': True })

@api_view(['GET'])
def report(request):
	token = request.GET.get('token')
	report = request.GET.get('report')
	if not token or not report:
		return Response({ 'data': 'Invalid parameters', 'status': False })
	if not Token.objects.filter(key=token).exists():
		return Response({ 'data': 'Invalid token', 'status': False })
	if not Report.objects.filter(id=report).exists():
		return Response({ 'data': 'Report not found', 'status': False })
	report = Report.objects.filter(id=report).first()
	report_serializer = ReportSerializer(report)
	return Response({ 'data': report_serializer.data, 'status': True })

@api_view(['POST'])
def submit_prediction(request):
	token = request.GET.get('token')
	report = request.GET.get('report')
	if not token or not report:
		return Response({ 'data': 'Invalid parameters', 'status': False })
	if not Token.objects.filter(key=token).exists():
		return Response({ 'data': 'Invalid token', 'status': False })
	if not Report.objects.filter(id=report).exists():
		return Response({ 'data': 'Report not found', 'status': False })
	token = Token.objects.filter(key=token).first()
	user = token.user
	report = Report.objects.filter(id=report).first()
	predicted_event = request.data.get('predicted-event')
	generated_text = request.data.get('generated-text')
	confidence_score = request.data.get('confidence-score')
	valid_until = request.data.get('valid-until')
	ai_model_version = request.data.get('ai-model-version')
	if not predicted_event or not generated_text or not confidence_score or not valid_until or not ai_model_version:
		return Response({ 'data': 'Fields are required', 'status': False })
	prediction = Prediction.objects.create(
		predicted_event=predicted_event,
		generated_text=generated_text,
		confidence_score=confidence_score,
		valid_until=valid_until,
		ai_model_version=ai_model_version,
		user=user,
		report=report
	)
	now = timezone.now()
	last_24_hours = timezone.now() - timedelta(hours=24)
	predictions = Prediction.objects.filter(timestamp__gte=last_24_hours, timestamp__lte=now).all()[::-1]
	predictions_serializer = PredictionSerializer(predictions, many=True)
	channel_layer = get_channel_layer()
	async_to_sync(channel_layer.group_send)(
		'predictions',
		{
			'type': 'send_prediction',
			'message': predictions_serializer.data,
		}
	)
	async_to_sync(channel_layer.group_send)(
		'notifications',
		{
			'type': 'send_notification',
			'message': {
				'data': f'{prediction.user} added prediction on {prediction.report.description}',
			},
		}
	)
	return Response({ 'data': 'Prediction has been submitted', 'status': True })

@api_view(['GET'])
def predictions(request):
	token = request.GET.get('token')
	if not token:
		return Response({ 'data': 'Invalid parameters', 'status': False })
	if not Token.objects.filter(key=token).exists():
		return Response({ 'data': 'Invalid token', 'status': False })
	now = timezone.now()
	last_24_hours = timezone.now() - timedelta(hours=24)
	predictions = Prediction.objects.filter(timestamp__gte=last_24_hours, timestamp__lte=now).all()[::-1]
	predictions_serializer = PredictionSerializer(predictions, many=True)
	return Response({ 'data': predictions_serializer.data, 'status': True })

@api_view(['GET'])
def prediction(request):
	token = request.GET.get('token')
	prediction = request.GET.get('prediction')
	if not token or not prediction:
		return Response({ 'data': 'Invalid parameters', 'status': False })
	if not Token.objects.filter(key=token).exists():
		return Response({ 'data': 'Invalid token', 'status': False })
	if not Prediction.objects.filter(id=prediction).exists():
		return Response({ 'data': 'Prediction not found', 'status': False })
	prediction = Prediction.objects.filter(id=prediction).first()
	prediction_serializer = PredictionSerializer(prediction)
	return Response({ 'data': prediction_serializer.data, 'status': True })

@api_view(['GET'])
def like_report_check(request):
	token = request.GET.get('token')
	report = request.GET.get('report')
	if not token or not report:
		return Response({ 'data': 'Invalid parameters', 'status': False })
	if not Token.objects.filter(key=token).exists():
		return Response({ 'data': 'Invalid token', 'status': False })
	if not Report.objects.filter(id=report).exists():
		return Response({ 'data': 'Report not found', 'status': False })
	token = Token.objects.filter(key=token).first()
	user = token.user
	report = Report.objects.filter(id=report).first()
	if ReportLike.objects.filter(report=report).filter(user=user).exists():
		return Response({ 'data': True, 'status': True })
	return Response({ 'data': False, 'status': True })

@api_view(['GET'])
def like_report(request):
	token = request.GET.get('token')
	report = request.GET.get('report')
	if not token or not report:
		return Response({ 'data': 'Invalid parameters', 'status': False })
	if not Token.objects.filter(key=token).exists():
		return Response({ 'data': 'Invalid token', 'status': False })
	if not Report.objects.filter(id=report).exists():
		return Response({ 'data': 'Report not found', 'status': False })
	token = Token.objects.filter(key=token).first()
	user = token.user
	report = Report.objects.filter(id=report).first()
	if ReportLike.objects.filter(report=report).filter(user=user).exists():
		return Response({ 'data': 'Bad request', 'status': False })
	report_like = ReportLike.objects.create(report=report, user=user)
	channel_layer = get_channel_layer()
	async_to_sync(channel_layer.group_send)(
		f'user_{str(report_like.report.user.id)}',
		{
			'type': 'send_notification',
			'message': {
				'data': f'{report_like.user.username} liked your report',
			},
		}
	)
	return Response({ 'data': True, 'status': True })

@api_view(['GET'])
def dislike_report(request):
	token = request.GET.get('token')
	report = request.GET.get('report')
	if not token or not report:
		return Response({ 'data': 'Invalid parameters', 'status': False })
	if not Token.objects.filter(key=token).exists():
		return Response({ 'data': 'Invalid token', 'status': False })
	if not Report.objects.filter(id=report).exists():
		return Response({ 'data': 'Report not found', 'status': False })
	token = Token.objects.filter(key=token).first()
	user = token.user
	report = Report.objects.filter(id=report).first()
	if ReportLike.objects.filter(report=report).filter(user=user).exists():
		ReportLike.objects.filter(report=report).filter(user=user).delete()
		return Response({ 'data': True, 'status': True })
	return Response({ 'data': 'Bad request', 'status': False })

@api_view(['GET'])
def like_prediction_check(request):
	token = request.GET.get('token')
	prediction = request.GET.get('prediction')
	if not token or not prediction:
		return Response({ 'data': 'Invalid parameters', 'status': False })
	if not Token.objects.filter(key=token).exists():
		return Response({ 'data': 'Invalid token', 'status': False })
	if not Prediction.objects.filter(id=prediction).exists():
		return Response({ 'data': 'Prediction not found', 'status': False })
	token = Token.objects.filter(key=token).first()
	user = token.user
	prediction = Prediction.objects.filter(id=prediction).first()
	if PredictionLike.objects.filter(prediction=prediction).filter(user=user).exists():
		return Response({ 'data': True, 'status': True })
	return Response({ 'data': False, 'status': True })

@api_view(['GET'])
def like_prediction(request):
	token = request.GET.get('token')
	prediction = request.GET.get('prediction')
	if not token or not prediction:
		return Response({ 'data': 'Invalid parameters', 'status': False })
	if not Token.objects.filter(key=token).exists():
		return Response({ 'data': 'Invalid token', 'status': False })
	if not Prediction.objects.filter(id=prediction).exists():
		return Response({ 'data': 'Prediction not found', 'status': False })
	token = Token.objects.filter(key=token).first()
	user = token.user
	prediction = Prediction.objects.filter(id=prediction).first()
	if PredictionLike.objects.filter(prediction=prediction).filter(user=user).exists():
		return Response({ 'data': 'Bad request', 'status': False })
	prediction_like = PredictionLike.objects.create(prediction=prediction, user=user)
	channel_layer = get_channel_layer()
	async_to_sync(channel_layer.group_send)(
		'user_{prediction_like.prediction.user.id}',
		{
			'type': 'send_notification',
			'message': {
				'data': f'{prediction_like.user.username} liked your prediction',
			},
		}
	)
	return Response({ 'data': True, 'status': True })

@api_view(['GET'])
def dislike_prediction(request):
	token = request.GET.get('token')
	prediction = request.GET.get('prediction')
	if not token or not prediction:
		return Response({ 'data': 'Invalid parameters', 'status': False })
	if not Token.objects.filter(key=token).exists():
		return Response({ 'data': 'Invalid token', 'status': False })
	if not Prediction.objects.filter(id=prediction).exists():
		return Response({ 'data': 'Prediction not found', 'status': False })
	token = Token.objects.filter(key=token).first()
	user = token.user
	prediction = Prediction.objects.filter(id=prediction).first()
	if PredictionLike.objects.filter(prediction=prediction).filter(user=user).exists():
		PredictionLike.objects.filter(prediction=prediction).filter(user=user).delete()
		return Response({ 'data': True, 'status': True })
	return Response({ 'data': 'Bad request', 'status': False })

@api_view(['POST'])
def submit_report_feedback(request):
	token = request.GET.get('token')
	report = request.GET.get('report')
	if not token or not report:
		return Response({ 'data': 'Invalid parameters', 'status': False })
	if not Token.objects.filter(key=token).exists():
		return Response({ 'data': 'Invalid token', 'status': False })
	if not Report.objects.filter(id=report).exists():
		return Response({ 'data': 'Report not found', 'status': False })
	token = Token.objects.filter(key=token).first()
	user = token.user
	report = Report.objects.filter(id=report).first()
	rating = request.data.get('rating')
	comment = request.data.get('comment')
	is_accurate = request.data.get('is-accurate')
	if not rating or not comment or not is_accurate:
		return Response({ 'data': 'Fields are required', 'status': False })
	feedback = Feedback.objects.create(
		rating=rating,
		comment=comment,
		is_accurate=is_accurate,
		user=user,
		report=report
	)
	channel_layer = get_channel_layer()
	async_to_sync(channel_layer.group_send)(
		f'user_{str(feedback.report.user.id)}',
		{
			'type': 'send_notification',
			'message': {
				'data': f'{feedback.user.username} added feedback on your report',
			},
		}
	)
	return Response({ 'data': 'Feedback has been submitted', 'status': True })

@api_view(['GET'])
def report_feedbacks(request):
	token = request.GET.get('token')
	report = request.GET.get('report')
	if not token or not report:
		return Response({ 'data': 'Invalid parameters', 'status': False })
	if not Token.objects.filter(key=token).exists():
		return Response({ 'data': 'Invalid token', 'status': False })
	if not Report.objects.filter(id=report).exists():
		return Response({ 'data': 'Report not found', 'status': False })
	report = Report.objects.filter(id=report).first()
	feedbacks = report.feedbacks
	feedbacks_serializer = FeedbackSerializer(feedbacks, many=True)
	return Response({ 'data': feedbacks_serializer.data, 'status': True })

@api_view(['POST'])
def submit_prediction_feedback(request):
	token = request.GET.get('token')
	prediction = request.GET.get('prediction')
	if not token or not prediction:
		return Response({ 'data': 'Invalid parameters', 'status': False })
	if not Token.objects.filter(key=token).exists():
		return Response({ 'data': 'Invalid token', 'status': False })
	if not Prediction.objects.filter(id=prediction).exists():
		return Response({ 'data': 'Prediction not found', 'status': False })
	token = Token.objects.filter(key=token).first()
	user = token.user
	prediction = Prediction.objects.filter(id=prediction).first()
	rating = request.data.get('rating')
	comment = request.data.get('comment')
	is_accurate = request.data.get('is-accurate')
	if not rating or not comment or not is_accurate:
		return Response({ 'data': 'Fields are required', 'status': False })
	feedback = Feedback.objects.create(
		rating=rating,
		comment=comment,
		is_accurate=is_accurate,
		user=user,
		prediction=prediction
	)
	channel_layer = get_channel_layer()
	async_to_sync(channel_layer.group_send)(
		f'user_{str(feedback.prediction.user.id)}',
		{
			'type': 'send_notification',
			'message': {
				'data': f'{feedback.user.username} added feedback on your prediction',
			},
		}
	)
	return Response({ 'data': 'Feedback has been submitted', 'status': True })

@api_view(['GET'])
def prediction_feedbacks(request):
	token = request.GET.get('token')
	prediction = request.GET.get('prediction')
	if not token or not prediction:
		return Response({ 'data': 'Invalid parameters', 'status': False })
	if not Token.objects.filter(key=token).exists():
		return Response({ 'data': 'Invalid token', 'status': False })
	if not Prediction.objects.filter(id=prediction).exists():
		return Response({ 'data': 'Prediction not found', 'status': False })
	prediction = Prediction.objects.filter(id=prediction).first()
	feedbacks = prediction.feedbacks
	feedbacks_serializer = FeedbackSerializer(feedbacks, many=True)
	return Response({ 'data': feedbacks_serializer.data, 'status': True })

@api_view(['POST'])
def submit_reply(request):
	token = request.GET.get('token')
	feedback = request.GET.get('feedback')
	if not token or not feedback:
		return Response({ 'data': 'Invalid parameters', 'status': False })
	if not Token.objects.filter(key=token).exists():
		return Response({ 'data': 'Invalid token', 'status': False })
	if not Feedback.objects.filter(id=feedback).exists():
		return Response({ 'data': 'Invalid feedback', 'status': False })
	token = Token.objects.filter(key=token).first()
	user = token.user
	feedback = Feedback.objects.filter(id=feedback).first()
	comment = request.data.get('comment')
	if not comment:
		return Response({ 'data': 'Fields are required', 'status': False })
	reply = Feedback.objects.create(
		comment=comment,
		parent_feedback=feedback,
		user=user
	)
	channel_layer = get_channel_layer()
	async_to_sync(channel_layer.group_send)(
		f'user_{str(reply.parent_feedback.user.id)}',
		{
			'type': 'send_notification',
			'message': {
				'data': f'{reply.user.username} replied to your feedback',
			},
		}
	)
	return Response({ 'data': 'Reply has been submitted', 'status': True })

@api_view(['GET'])
def replies(request):
	token = request.GET.get('token')
	feedback = request.GET.get('feedback')
	if not token or not feedback:
		return Response({ 'data': 'Invalid parameters', 'status': False })
	if not Token.objects.filter(key=token).exists():
		return Response({ 'data': 'Invalid token', 'status': False })
	if not Feedback.objects.filter(id=feedback).exists():
		return Response({ 'data': 'Invalid feedback', 'status': False })
	feedback = Feedback.objects.filter(id=feedback).first()
	replies = feedback.replies
	replies_serializer = FeedbackSerializer(replies, many=True)
	return Response({ 'data': replies_serializer.data, 'status': True })

@api_view(['POST'])
def explore(request):
	token = request.GET.get('token')
	if not token:
		return Response({ 'data': 'Invalid parameters', 'status': False })
	location = request.data.get('location')
	if not location:
		return Response({ 'data': 'Fields are required', 'status': False })
	last_24_hours = timezone.now() - timedelta(hours=24)
	recent_reports = Report.objects.filter(
		location__icontains=location,
		timestamp__gte=last_24_hours,
		status='active'
	)
	if not recent_reports.exists():
		return Response({ 'data': 'Not enough data', 'status': False })
	reports_analysis = analysis(recent_reports)
	return Response({ 'data': reports_analysis, 'status': True })
