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


class CustomUIDModel(models.Model):
    uid = models.CharField(max_length=500)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

# class CustomUserModel()
# from django.conf import settings
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from rest_framework.authtoken.models import Token
#
# @receiver(post_save, sender=settings.AUTH_USER_MODEL)
# def create_auth_token(sender, instance=None, created=False, **kwargs):
#     if created:
#         Token.objects.create(user=instance)
