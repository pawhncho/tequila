from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField

# Create your models here.
class Notification(models.Model):
	actor = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
	report = models.ForeignKey('Report', on_delete=models.CASCADE, blank=True, null=True, db_index=True)
	report_like = models.ForeignKey('ReportLike', on_delete=models.CASCADE, blank=True, null=True, db_index=True)
	prediction = models.ForeignKey('Prediction', on_delete=models.CASCADE, blank=True, null=True, db_index=True)
	prediction_like = models.ForeignKey('PredictionLike', on_delete=models.CASCADE, blank=True, null=True, db_index=True)
	feedback = models.ForeignKey('Feedback', on_delete=models.CASCADE, blank=True, null=True, db_index=True)
	action_type = models.CharField(max_length=16, db_index=True) # Report, ReportLike, Prediction, PredictionLike, Feedback
	message = models.CharField(max_length=225, db_index=True)
	timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
	user = models.ManyToManyField(User, related_name='notifications', db_index=True)

class Profile(models.Model):
	phone_number = models.CharField(max_length=255, blank=True, null=True, db_index=True)
	profile_picture = CloudinaryField('image', folder='profile-pictures', blank=True, null=True)
	location = models.CharField(max_length=255, blank=True, null=True, db_index=True)
	timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
	last_modified = models.DateTimeField(auto_now_add=True, db_index=True)
	verification_status = models.BooleanField(default=False, db_index=True)
	notification_status = models.BooleanField(default=False, db_index=True)
	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', db_index=True)

class Report(models.Model):
	location = models.CharField(max_length=225, blank=True, null=True, db_index=True)
	latitude = models.DecimalField(max_digits=9, decimal_places=6, db_index=True)
	longitude = models.DecimalField(max_digits=9, decimal_places=6, db_index=True)
	report_type = models.CharField(max_length=255, db_index=True) # e.g., traffic, noise, crowd
	description = models.TextField(blank=True, null=True, db_index=True)
	timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
	status = models.CharField(max_length=255, db_index=True) # e.g., active, expired
	sensor_data = models.JSONField(default=dict, blank=True, null=True, db_index=True)
	verification_status = models.BooleanField(default=False, db_index=True)
	rating = models.FloatField(blank=True, null=True, db_index=True)
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports', db_index=True)

	def save(self, *args, **kwargs):
		super().save(*args, **kwargs)
		notification = Notification.objects.create(actor=self.user, report=self, action_type='Report', message=f'{self.user} reported {self.description} at {self.location}')
		notification.user.set(User.objects.all())

class ReportLike(models.Model):
	timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
	report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='likes', db_index=True)
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='liked_reports', db_index=True)

	class Meta:
		unique_together = ('report', 'user')

	def save(self, *args, **kwargs):
		if self.report.user == self.user:
			return
		else:
			super().save(*args, **kwargs)
			notification = Notification.objects.create(actor=self.user, report_like=self, action_type='ReportLike', message=f'{self.user} liked your report')
			notification.user.set([self.report.user])

class Prediction(models.Model):
	predicted_event = models.CharField(max_length=255, db_index=True)
	generated_text = models.TextField(db_index=True)
	confidence_score = models.FloatField(db_index=True) # 0-1 indicating AI confidence
	valid_until = models.DateTimeField(auto_now_add=True, blank=True, null=True, db_index=True)
	ai_model_version = models.CharField(max_length=255, default='GPT-4', db_index=True)
	timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='predictions', blank=True, null=True, db_index=True)
	report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='predictions', db_index=True)

	def save(self, *args, **kwargs):
		super().save(*args, **kwargs)
		notification = Notification.objects.create(actor=self.user, prediction=self, action_type='Prediction', message=f'{self.user} added prediction on {self.report.description}')
		notification.user.set(User.objects.all())

class PredictionLike(models.Model):
	timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
	prediction = models.ForeignKey(Prediction, on_delete=models.CASCADE, related_name='likes', db_index=True)
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='liked_predictions', db_index=True)

	class Meta:
		unique_together = ('prediction', 'user')

	def save(self, *args, **kwargs):
		if self.prediction.user == self.user:
			return
		else:
			super().save(*args, **kwargs)
			notification = Notification.objects.create(actor=self.user, prediction_like=self, action_type='PredictionLike', message=f'{self.user} liked your prediction')
			notification.user.set([self.prediction.user])

class Feedback(models.Model):
	rating = models.IntegerField(null=True, blank=True, db_index=True)
	comment = models.TextField(null=True, blank=True, db_index=True)
	is_accurate = models.BooleanField(default=False, null=True, blank=True, db_index=True)
	timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
	parent_feedback = models.ForeignKey('self', on_delete=models.CASCADE, related_name='replies', blank=True, null=True, db_index=True)
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks', blank=True, null=True, db_index=True)
	prediction = models.ForeignKey(Prediction, on_delete=models.CASCADE, related_name='feedbacks', blank=True, null=True, db_index=True)
	report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='feedbacks', blank=True, null=True, db_index=True)

	def save(self, *args, **kwargs):
		if self.prediction:
			super().save(*args, **kwargs)
			notification = Notification.objects.create(actor=self.user, feedback=self, action_type='Feedback', message=f'{self.user} added feedback on your prediction')
			notification.user.set([self.prediction.user])
		elif self.report:
			super().save(*args, **kwargs)
			notification = Notification.objects.create(actor=self.user, feedback=self, action_type='Feedback', message=f'{self.user} added feedback on your report')
			notification.user.set([self.report.user])
		elif self.parent_feedback:
			super().save(*args, **kwargs)
			notification = Notification.objects.create(actor=self.user, feedback=self, action_type='Feedback', message=f'{self.user} replied to your feedback')
			notification.user.set([self.parent_feedback.user])
