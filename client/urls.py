from django.urls import path
from . import views

# Create your urls here.
urlpatterns = [
	path('register-admin/', views.register_admin),
	path('reset-password/', views.reset_password_page),
	path('login/', views.login),
	path('register/', views.register),
	path('forgot-password/', views.forgot_password),
	path('reset-password/<token>/', views.reset_password),
	path('send-verification-email/', views.send_verification_email),
	path('verify-email/<token>/', views.verify_email),
	path('profile/', views.profile),
	path('notifications/', views.notifications),
	path('turn-on-notifications/', views.turn_on_notifications),
	path('turn-off-notifications/', views.turn_off_notifications),
	path('update-profile/', views.update_profile),
	path('submit-report/', views.submit_report),
	path('reports/', views.reports),
	path('report/', views.report),
	path('submit-prediction/', views.submit_prediction),
	path('predictions/', views.predictions),
	path('prediction/', views.prediction),
	path('like-report-check/', views.like_report_check),
	path('like-report/', views.like_report),
	path('dislike-report/', views.dislike_report),
	path('like-prediction-check/', views.like_prediction_check),
	path('like-prediction/', views.like_prediction),
	path('dislike-prediction/', views.dislike_prediction),
	path('submit-report-feedback/', views.submit_report_feedback),
	path('report-feedbacks/', views.report_feedbacks),
	path('submit-prediction-feedback/', views.submit_prediction_feedback),
	path('prediction-feedbacks/', views.prediction_feedbacks),
	path('submit-reply/', views.submit_reply),
	path('replies/', views.replies),
	path('explore/', views.explore),
]
