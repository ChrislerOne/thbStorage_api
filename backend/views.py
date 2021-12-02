import json
import random

import django.core.exceptions
import rest_framework.exceptions
from django.contrib.auth.models import User
from django.core import serializers
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser

import backend.models
from backend.serializer import FileSerializer
from backend.models import FileModel, DirectoryModel, CustomUIDModel
from backend.firebase import get_user, get_uid
from rest_framework.exceptions import *
from django.core.exceptions import *


def create_user_if_not_existent(uid: str):
    firebase_user = get_user(uid)
    if CustomUIDModel.objects.filter(uid=firebase_user.uid):
        uid_obj = CustomUIDModel.objects.get(uid=firebase_user.uid)
        user = uid_obj.user
    else:
        # User Object neccesary for token creation
        user = User.objects.create(email=firebase_user.email, username=firebase_user.email,
                                   password=str(str(random.randbytes(14))))
        CustomUIDModel.objects.create(uid=firebase_user.uid, user=user)
    return user


# Create your views here.
class FileViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows files to be viewed or edited
    """
    queryset = FileModel.objects.all()
    serializer_class = FileSerializer
    parser_class = (MultiPartParser,)

    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # TODO: Abfrage nach verfügbaren Speicherplatz für User

        upload = self.request.FILES['content']
        upload_data = self.request.data

        uid = get_uid(upload_data['id_token'])
        user = create_user_if_not_existent(uid)

        # TODO: Directory erstellen, falls nicht vorhanden und dann setzen.
        directory = DirectoryModel.objects.get(pk=1)

        file = FileModel()
        file.name = upload_data['name']
        file.location = upload_data['location']
        file.content = upload
        file.checksum = ''
        # TODO: get directory of user and match it with request
        file.directory = directory
        # TODO: Users Account erhalten und dementsprechend eintragen
        file.owner = user
        # file.owner = upload_data['user']

        if file.location != 'null':
            file.content.name = str(uid) + '/' + file.location + '/' + file.name
        else:
            file.content.name = str(uid) + '/' + file.name

        serializer = FileSerializer(data=file.__dict__)
        if serializer.is_valid():
            serializer.save()
        else:
            print(serializer.errors)
            print(file.__dict__)
            return Response(serializer.errors, status=400)

        return Response(status=201)

    def list(self, request, *args, **kwargs):
        try:
            id_token = request.GET.get("id_token", '')
            uid = get_uid(id_token)
            user = CustomUIDModel.objects.filter(uid=uid).get().user
            all_files = FileModel.objects.filter(owner_id=user.pk)
            response = serializers.serialize('json', all_files.all())
            return Response(data=response, status=status.HTTP_200_OK)
        except:
            return Response(data=[], status=status.HTTP_200_OK)
