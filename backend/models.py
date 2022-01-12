from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from datetime import datetime


class CustomUIDModel(models.Model):
    uid = models.CharField(max_length=500)
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class FileNewModel(models.Model):
    fileName = models.CharField(max_length=500)
    location = models.CharField(blank=True, max_length=500, null=True, default='')
    content = models.FileField()
    checksum = models.CharField(max_length=64, null=True)
    last_changed = models.DateTimeField(default=timezone.now())
    isPublic = models.BooleanField(default=False)
    owner = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
