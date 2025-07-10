from django.contrib import admin
from .models import Notification, Profile, Report, ReportLike, Prediction, PredictionLike, Feedback

# Register your models here.
admin.site.register(Notification)
admin.site.register(Profile)
admin.site.register(Report)
admin.site.register(ReportLike)
admin.site.register(Prediction)
admin.site.register(PredictionLike)
admin.site.register(Feedback)
