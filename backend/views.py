import json
import os
import random
from django.utils import timezone
import django.core.exceptions
import rest_framework.exceptions
from django.contrib.auth.models import User
from django.core import serializers
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser

import backend.models
from backend.serializer import FileSerializer, FileNewSerializer
from backend.models import FileModel, DirectoryModel, CustomUIDModel, FileNewModel
from backend.firebase import get_user, get_uid
from rest_framework.exceptions import *
from django.core.exceptions import *
from django.http import FileResponse, HttpResponse

from thbStorage_API import settings


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

    # def perform_create(self, serializer):
    #     # TODO: Abfrage nach verfügbaren Speicherplatz für User
    #
    #     upload = self.request.FILES['content']
    #     upload_data = self.request.data
    #
    #     uid = get_uid(upload_data['id_token'])
    #     user = create_user_if_not_existent(uid)
    #
    #     # TODO: Directory erstellen, falls nicht vorhanden und dann setzen.
    #     directory = DirectoryModel.objects.get(pk=1)
    #
    #     file = FileModel()
    #     file.name = upload_data['name']
    #     file.location = upload_data['location']
    #     file.content = upload
    #     file.checksum = ''
    #     # TODO: get directory of user and match it with request
    #     file.directory = directory
    #     # TODO: Users Account erhalten und dementsprechend eintragen
    #     file.owner = user
    #     # file.owner = upload_data['user']
    #
    #     if file.location != 'null':
    #         file.content.name = str(uid) + '/' + file.location + '/' + file.name
    #     else:
    #         file.content.name = str(uid) + '/' + file.name
    #
    #     serializer = FileSerializer(data=file.__dict__)
    #     if serializer.is_valid():
    #         serializer.save()
    #     else:
    #         print(serializer.errors)
    #         print(file.__dict__)
    #         return Response(serializer.errors, status=400)
    #
    #     return Response(status=201)

    # def list(self, request, *args, **kwargs):
    #     id_token = request.GET.get("id_token", '')
    #     uid = get_uid(id_token)
    #     if uid is None:
    #         return Response({'status': 'not authorized'}, status=status.HTTP_403_FORBIDDEN)
    #
    #     user = CustomUIDModel.objects.filter(uid=uid).get().user
    #     all_files = FileModel.objects.filter(owner_id=user.pk)
    #     response = serializers.serialize('json', all_files)
    #     response = json.loads(response)
    #     for d in response:
    #         del d['model']
    #         del d['pk']
    #     return Response(data=response, status=status.HTTP_200_OK)


def json_from_path(path, uid, user):
    # d = {'name': os.path.basename(path)}
    d = {}
    absolute_path = f'{settings.MEDIA_ROOT}/{uid}{path}'
    print(absolute_path)
    if os.path.isdir(absolute_path):
        d['type'] = "directory"
        d['location'] = path
        d['folderName'] = os.path.basename(path).replace(uid, '')
        d['children'] = [json_from_path(os.path.join(path, x),uid, user) for x in os.listdir(absolute_path)]
    elif os.path.isfile(absolute_path):
        # ansolute_path = f'{settings.MEDIA_ROOT}/{uid}{path}'
        print(os.path.dirname(path))
        temp = FileNewModel.objects.get(owner_id=user.pk, location=os.path.dirname(path), fileName=os.path.basename(path))
        try:
            d['type'] = "file"
            d['location'] = path
            d['checksum'] = temp.checksum
            d['last_changed'] = temp.last_changed
            d['isPublic'] = temp.isPublic
        except:
            return 'error'
    return d


@api_view(['GET'])
def files_list(request):
    id_token = request.GET.get("id_token", '')
    uid = get_uid(id_token)
    if uid is None:
        return Response({'status': 'not authorized'}, status=status.HTTP_403_FORBIDDEN)

    user = CustomUIDModel.objects.filter(uid=uid).get().user

    json_data = json_from_path('/', uid, user)

    if json_data is 'error':
        return Response(data={'status': 'Database error'}, status=status.HTTP_400_BAD_REQUEST)

    return Response(data=json_data, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_file(request):
    id_token = request.GET.get("id_token", '')
    uid = get_uid(id_token)
    if uid is None:
        return Response({'status': 'not authorized'}, status=status.HTTP_403_FORBIDDEN)
    filepath = ''
    try:
        filepath = request.data['filepath']
    except KeyError:
        return Response({'status': 'missing parameter'}, status=status.HTTP_400_BAD_REQUEST)

    user = CustomUIDModel.objects.filter(uid=uid).get().user

    temp = FileNewModel.objects.filter(owner_id=user.pk, content=f'{uid}{filepath}').first()
    file = open(f'{settings.MEDIA_ROOT}/{uid}{filepath}', 'r')
    file.close()
    filename = os.path.basename(file.name)
    print(temp.fileName)
    json_data = {
        'fileName': filename,
        'location': file.name.replace(f'{settings.MEDIA_ROOT}/{uid}', ''),
        'content': file.name,
        'checksum': temp.checksum,
        'last_changed': temp.last_changed,
        'isPublic': temp.isPublic,
    }
    return Response(data=json_data, status=status.HTTP_200_OK)


@api_view(['POST'])
def upload_file(request):
    # TODO: Abfrage nach verfügbaren Speicherplatz für User

    upload = request.FILES['content']
    upload_data = request.data

    id_token = request.GET.get("id_token", '')
    uid = get_uid(id_token)
    if uid is None:
        return Response({'status': 'not authorized'}, status=status.HTTP_403_FORBIDDEN)
    user = create_user_if_not_existent(uid)

    # TODO: Directory erstellen, falls nicht vorhanden und dann setzen.

    fileNew = FileNewModel()
    fileNew.fileName = upload_data['name']
    fileNew.location = upload_data['location']
    fileNew.content = upload
    fileNew.checksum = upload_data['checksum']
    # TODO: get directory of user and match it with request

    # TODO: Users Account erhalten und dementsprechend eintragen

    fileNew.owner = user

    if fileNew.location != 'null':
        fileNew.content.name = str(uid) + '/' + fileNew.location + '/' + fileNew.fileName
    else:
        fileNew.content.name = str(uid) + '/' + fileNew.fileName

    fileName = fileNew.content.name.replace(uid, '')
    fileNew.fileName = fileName.replace('/', '')
    serializer = FileNewSerializer(data=fileNew.__dict__)
    if serializer.is_valid():
        fileNew.save()
    else:
        print(serializer.errors)
        print(fileNew.__dict__)
        return Response(serializer.errors, status=400)

    return Response(status=201)


@api_view(['GET'])
def rename_filename(request):
    id_token = request.GET.get("id_token", '')
    uid = get_uid(id_token)
    if uid is None:
        return Response({'status': 'not authorized'}, status=status.HTTP_403_FORBIDDEN)

    upload_data = request.data
    fileName = upload_data['name']
    newFileName = upload_data['newName']
    location = upload_data['location']

    user = CustomUIDModel.objects.filter(uid=uid).get().user
    try:
        file = FileNewModel.objects.get(owner_id=user.pk, location=location, fileName=fileName)
    except FileNewModel.DoesNotExist:
        file = None
        return Response(data={'status': 'File not Exist'}, status=status.HTTP_404_NOT_FOUND)
    path = f'{settings.MEDIA_ROOT}/{uid}{location}{fileName}'
    new_file_path = f'{settings.MEDIA_ROOT}/{uid}{location}{newFileName}'
    os.rename(path, new_file_path)
    # print(f'{path} \n{new_file_path}')
    file.fileName = newFileName
    file.last_changed = timezone.now()
    file.content.name = f'{uid}/{newFileName}'
    file.save()

    return Response(data={'status': 'updated'}, status=status.HTTP_200_OK)


@api_view(['GET'])
def create_directory(request):
    id_token = request.GET.get("id_token", '')
    uid = get_uid(id_token)
    if uid is None:
        return Response({'status': 'not authorized'}, status=status.HTTP_403_FORBIDDEN)

    upload_data = request.data
    location = upload_data['location']
    name = upload_data['name']

    path = f'{settings.MEDIA_ROOT}/{uid}{location}'
    new_dir_path = f'{settings.MEDIA_ROOT}/{uid}{location}/{name}'

    if not os.path.exists(new_dir_path):
        os.makedirs(new_dir_path)
    else:
        return Response(data={'status': 'directory already exists'}, status=status.HTTP_400_BAD_REQUEST)

    return Response(status=status.HTTP_201_CREATED)


@api_view(['GET'])
def rename_directory(request):
    id_token = request.GET.get("id_token", '')
    uid = get_uid(id_token)
    if uid is None:
        return Response({'status': 'not authorized'}, status=status.HTTP_403_FORBIDDEN)

    upload_data = request.data
    location = upload_data['location']
    name = upload_data['name']
    new_name = upload_data['newName']

    path = f'{settings.MEDIA_ROOT}/{uid}{location}{name}'
    new_dir_path = f'{settings.MEDIA_ROOT}/{uid}{location}{new_name}'

    if os.path.exists(path):
        os.rename(path, new_dir_path)
    else:
        return Response(data={'status': 'directory not exists'}, status=status.HTTP_400_BAD_REQUEST)

    return Response(status=status.HTTP_201_CREATED)
