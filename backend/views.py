import os
import random
import hashlib
import re
import string
import unicodedata

from django.utils import timezone
from django.contrib.auth.models import User
from django.utils.functional import keep_lazy_text
from rest_framework.decorators import api_view
from rest_framework.response import Response

from backend.serializer import FileNewSerializer
from backend.models import CustomUIDModel, FileNewModel
from django.core.exceptions import ObjectDoesNotExist
from backend.firebase import get_user, get_uid
from rest_framework.exceptions import *
from django.http import FileResponse

from thbStorage_API import settings


@keep_lazy_text
def slugify(value, allow_unicode=False):
    """
    Convert to ASCII if 'allow_unicode' is False. Convert spaces to hyphens.
    Remove characters that aren't alphanumerics, underscores, or hyphens.
    Convert to lowercase. Also strip leading and trailing whitespace.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s\.-]', '', value.lower()).strip()
    return re.sub(r'[-\s]+', '_', value)


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


def check_auth(id_token):
    uid = get_uid(id_token)
    if uid is None:
        return Response({'status': 'not authorized'}, status=status.HTTP_403_FORBIDDEN)
    return uid


def json_from_path(path, uid, user):
    # d = {'name': os.path.basename(path)}
    d = {}
    absolute_path = f'{settings.MEDIA_ROOT}/{uid}{path}'
    #print(absolute_path)
    if os.path.isdir(absolute_path):
        try:
            d['type'] = "directory"
            d['location'] = path
            d['folderName'] = os.path.basename(path).replace(uid, '')
            d['children'] = [json_from_path(os.path.join(path, x), uid, user) for x in os.listdir(absolute_path)]
        except FileNotFoundError:
            return Response({'status': 'File not Found'}, status=status.HTTP_404_NOT_FOUND)
    elif os.path.isfile(absolute_path):
        # ansolute_path = f'{settings.MEDIA_ROOT}/{uid}{path}'
        #print(os.path.dirname(path))
        try:
            temp = FileNewModel.objects.get(owner_id=user.pk, location=os.path.dirname(path),
                                            fileName=os.path.basename(path))
        except ObjectDoesNotExist:
            return Response({'status': 'Requested file does not exist!'}, status=status.HTTP_404_NOT_FOUND)

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
    uid = check_auth(request.GET.get("id_token", ''))

    user = CustomUIDModel.objects.filter(uid=uid).get().user

    json_data = json_from_path('/', uid, user)

    if json_data == 'error':
        return Response(data={'status': 'Database error'}, status=status.HTTP_400_BAD_REQUEST)

    return Response(data=json_data, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
def files_list_by_path(request):
    uid = check_auth(request.GET.get("id_token", ''))

    user = CustomUIDModel.objects.filter(uid=uid).get().user

    try:
        filepath = request.data['filepath']
    except KeyError:
        return Response({'status': 'missing parameter'}, status=status.HTTP_400_BAD_REQUEST)

    json_data = json_from_path(filepath, uid, user)

    if json_data == 'error':
        return Response(data={'status': 'Database error'}, status=status.HTTP_400_BAD_REQUEST)

    return Response(data=json_data, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
def get_specific_file(request):
    uid = check_auth(request.GET.get("id_token", ''))

    try:
        filepath = request.data['filepath']
    except KeyError:
        return Response({'status': 'missing parameter'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = CustomUIDModel.objects.filter(uid=uid).get().user
        file = FileNewModel.objects.get(owner_id=user.pk, location=os.path.dirname(filepath),
                                        fileName=os.path.basename(filepath))
    except FileNewModel.DoesNotExist:
        return Response(data={'status': 'File not Exist'}, status=status.HTTP_404_NOT_FOUND)

    try:
        file_handle = file.content.open()
    except FileNotFoundError:
        return Response(data={'status': 'File not Exist'}, status=status.HTTP_404_NOT_FOUND)

    response = FileResponse(file_handle, status=status.HTTP_200_OK, filename='test')
    response['Content-Length'] = file.content.size
    response['X-Content-Check.Sum'] = file.checksum
    response['X-Content-File-Name'] = file.fileName
    response['X-Content-Last-Changed'] = file.last_changed
    response['X-Content-Location'] = file.location
    response['X-Content-Is-Public'] = file.isPublic
    response['Content-Disposition'] = 'attachment; filename="%s"' % file.content.name

    return response


@api_view(['GET', 'POST'])
def get_file(request):
    uid = check_auth(request.GET.get("id_token", ''))

    try:
        filepath = request.data['filepath']
    except KeyError:
        return Response({'status': 'missing parameter'}, status=status.HTTP_400_BAD_REQUEST)

    user = CustomUIDModel.objects.filter(uid=uid).get().user
    try:
        temp = FileNewModel.objects.get(owner_id=user.pk, content=f'{uid}{filepath}')
    except ObjectDoesNotExist:
        return Response({'status': 'Requested file does not exist!'}, status=status.HTTP_404_NOT_FOUND)

    file = open(f'{settings.MEDIA_ROOT}/{uid}{filepath}', 'r')
    file.close()
    filename = os.path.basename(file.name)
    # print(temp.fileName)
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

    try:
        upload = request.FILES['content']
        upload_data = request.data
    except KeyError:
        return Response({'status': 'missing parameter'}, status=status.HTTP_400_BAD_REQUEST)

    uid = check_auth(request.GET.get("id_token", ''))
    try:
        user = CustomUIDModel.objects.filter(uid=uid).get().user
    except ObjectDoesNotExist:
        return Response({'status': 'User not exist'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        fileNew = FileNewModel()
        fileNew.fileName = upload_data['name']
        fileNew.location = upload_data['location']
        fileNew.content = upload
        fileNew.checksum = upload_data['checksum']
        fileNew.owner = user
    except KeyError:
        return Response({'status': 'missing parameter'}, status=status.HTTP_400_BAD_REQUEST)

    fileName = fileNew.content.name.replace(uid, '')
    if fileNew.location != 'null':
        fileName = fileName.replace(fileNew.location, '')
    fileName = fileName.replace('/', '')

    ownHash = hashlib.sha1(
        str(random.choices(string.ascii_uppercase + string.digits, k=10)).encode("UTF-8")).hexdigest()[
              :5]

    fileName = slugify(fileName)

    if FileNewModel.objects.filter(fileName=fileName, location=fileNew.location, owner_id=user.ok):
        rawName = fileName.split('.')
        rawName[0] = str(rawName[0]) + '_' + str(ownHash)
        fileName = '.'.join(rawName)

    if fileNew.location != 'null':
        fileNew.content.name = os.sep.join([str(uid), fileNew.location, fileName])
    else:
        fileNew.content.name = os.sep.join([str(uid), fileName])

    fileNew.fileName = fileName

    serializer = FileNewSerializer(data=fileNew.__dict__)
    if serializer.is_valid():
        fileNew.save()
    else:
        #print(serializer.errors)
        #print(fileNew.__dict__)
        return Response(serializer.errors, status=400)

    return Response(status=201)


@api_view(['GET', 'POST'])
def rename_filename(request):
    uid = check_auth(request.GET.get("id_token", ''))
    try:
        owid = CustomUIDModel.objects.filter(uid=uid).get().user.pk
    except ObjectDoesNotExist:
        return Response({'status': 'User not exist'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        upload_data = request.data
        fileName = upload_data['name']
        newFileName = upload_data['newName']
        location = upload_data['location']
    except KeyError:
        return Response({'status': 'missing parameter'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        file = FileNewModel.objects.get(owner_id=owid, location=location, fileName=fileName)
        if FileNewModel.objects.filter(fileName=newFileName, location=location, owner_id=owid).exists():
            rawName = newFileName.split('.')
            ownHash = hashlib.sha1(
                str(random.choices(string.ascii_uppercase + string.digits, k=10)).encode("UTF-8")).hexdigest()[
                      :10]
            rawName[0] = str(rawName[0]) + str(ownHash)
            newFileName = slugify('.'.join(rawName))

    except ObjectDoesNotExist:
        return Response(data={'status': 'File not exist'}, status=status.HTTP_404_NOT_FOUND)

    path = f'{settings.MEDIA_ROOT}/{uid}{location}{fileName}'
    new_file_path = f'{settings.MEDIA_ROOT}/{uid}{location}{newFileName}'
    os.rename(path, new_file_path)
    file.fileName = newFileName
    file.last_changed = timezone.now()
    if location == '/':
        file.content.name = os.sep.join([str(uid), newFileName])
    else:
        file.content.name = os.sep.join([str(uid), location, newFileName])
    file.save()

    return Response(data={'status': 'updated'}, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
def create_directory(request):
    uid = check_auth(request.GET.get("id_token", ''))
    try:
        owid = CustomUIDModel.objects.filter(uid=uid).get().user.pk
    except ObjectDoesNotExist:
        return Response({'status': 'User not exist'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        upload_data = request.data
        location = upload_data['location']
        name = upload_data['name']
    except KeyError:
        return Response({'status': 'missing parameter'}, status=status.HTTP_400_BAD_REQUEST)

    path = f'{settings.MEDIA_ROOT}/{uid}{location}'
    new_dir_path = f'{settings.MEDIA_ROOT}/{uid}{location}/{name}'

    if not os.path.exists(new_dir_path):
        os.makedirs(new_dir_path)
    else:
        return Response(data={'status': 'directory already exists'}, status=status.HTTP_400_BAD_REQUEST)

    return Response(status=status.HTTP_201_CREATED)


def rename_content_file_directory_in_DB(obj: FileNewModel, new_location: str):
    try:
        uid = CustomUIDModel.objects.filter(pk=obj.owner.id).get().user.uid
        obj.content.name = os.sep.join([str(uid), new_location, obj.fileName])
        obj.save()
        return True
    except:
        return False


@api_view(['GET', 'POST'])
def rename_directory(request):
    uid = check_auth(request.GET.get("id_token", ''))
    try:
        owid = CustomUIDModel.objects.filter(uid=uid).get().user.pk
    except ObjectDoesNotExist:
        return Response({'status': 'User not exist'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        upload_data = request.data
        location = list(upload_data['location'])
        newLocation = slugify(upload_data['newLocation'])
    except KeyError:
        return Response({'status': 'missing parameter'}, status=status.HTTP_400_BAD_REQUEST)

    current_absolute_location = os.sep.join(location)
    path = os.sep.join([settings.MEDIA_ROOT, uid, current_absolute_location])

    location[-1] = newLocation
    new_absolute_location = os.sep.join(location)
    new_dir_path = os.sep.join([settings.MEDIA_ROOT, uid, new_absolute_location])

    if os.path.exists(path):
        os.rename(path, new_dir_path)
    else:
        return Response(data={'status': 'directory not exists'}, status=status.HTTP_400_BAD_REQUEST)

    rec_list = list(FileNewModel.objects.get(location__st="/" + str(current_absolute_location), owner_id=owid))

    try:
        for obj in FileNewModel.objects.get(location=location, owner_id=owid):
            if not rename_content_file_directory_in_DB(obj, new_absolute_location):
                raise Exception

    except:
        for obj in rec_list:
            rename_content_file_directory_in_DB(obj, obj.location)
        return Response(status=status.HTTP_400_BAD_REQUEST, data={'status': 'Directory name could not be changed!'})

    return Response(status=status.HTTP_201_CREATED)
