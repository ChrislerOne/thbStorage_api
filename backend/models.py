from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from datetime import datetime


class DirectoryModel(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    directory = models.ForeignKey('self', on_delete=models.PROTECT, null=True)


# Model named more precisely to avoid potential overwriting of the built-in File class
class FileModel(models.Model):
    name = models.CharField(max_length=500)
    location = models.CharField(blank=True, max_length=500, null=True, default='')
    content = models.FileField()
    checksum = models.CharField(max_length=64, null=True)
    directory = models.ForeignKey(DirectoryModel, on_delete=models.PROTECT, null=True)
    last_changed = models.DateTimeField(default=timezone.now())
    isPublic = models.BooleanField(default=False)
    owner = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    # TODO: Downloadpath
