import os
import random
import hashlib
import re
import string
import unicodedata
import shutil

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
    value = re.sub(r'[^\w\s.-]', '', value).strip()
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
    # absolute_path = f'{settings.MEDIA_ROOT}/{uid}{path}'
    # TODO: CHECK IF IT WORKS
    absolute_path = os.sep.join([settings.MEDIA_ROOT, uid, path])
    # print(absolute_path)
    if os.path.isdir(absolute_path):
        try:
            d['type'] = "directory"
            d['location'] = path
            d['name'] = os.path.basename(absolute_path)
            d['children'] = [json_from_path(os.path.join(path, x), uid, user) for x in os.listdir(absolute_path)]
        except FileNotFoundError:
            return Response({'status': 'File not Found'}, status=status.HTTP_404_NOT_FOUND)
    elif os.path.isfile(absolute_path):
        # ansolute_path = f'{settings.MEDIA_ROOT}/{uid}{path}'
        # print(os.path.dirname(path))
        try:
            temp = FileNewModel.objects.get(owner_id=user.pk, location=os.path.dirname(path),
                                            fileName=os.path.basename(path))
        except ObjectDoesNotExist:
            return Response({'status': 'Requested file does not exist!'}, status=status.HTTP_404_NOT_FOUND)

        try:
            d['type'] = "file"
            d['name'] = temp.fileName
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
    try:
        user = CustomUIDModel.objects.filter(uid=uid).get().user
    except ObjectDoesNotExist:
        return Response({'status': 'Requested user does not exist!'}, status=status.HTTP_404_NOT_FOUND)

    json_data = json_from_path('/', uid, user)

    if json_data == 'error':
        return Response(data={'status': 'Database error'}, status=status.HTTP_400_BAD_REQUEST)

    return Response(data=json_data, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
def files_list_by_path(request):
    uid = check_auth(request.GET.get("id_token", ''))
    try:
        user = CustomUIDModel.objects.filter(uid=uid).get().user
    except ObjectDoesNotExist:
        return Response({'status': 'Requested user does not exist!'}, status=status.HTTP_404_NOT_FOUND)

    try:
        # TODO: CHECK IF IT WORKS
        file_list = request.data['filepath'].split(';')
        filepath = "/" + str(os.sep.join(file_list))
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
        # TODO: CHECK IF IT WORKS
        file_list = request.data['filepath'].split(';')
        name = request.data['name']
        filepath = str(os.sep.join(file_list))
        location = "/" + filepath.replace(name, '')
        if location == '':
            location = '/'
    except KeyError:
        return Response({'status': 'missing parameter'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        print(file_list)
        print(name)
        print(filepath)
        print(location)
        user = CustomUIDModel.objects.filter(uid=uid).get().user
        file = FileNewModel.objects.get(owner_id=user.pk, location=location,
                                        fileName=name)
    except FileNewModel.DoesNotExist:
        return Response(data={'status': 'File not Exist'}, status=status.HTTP_404_NOT_FOUND)

    try:
        file_handle = file.content.open()
    except FileNotFoundError:
        return Response(data={'status': 'File not Exist'}, status=status.HTTP_404_NOT_FOUND)

    response = FileResponse(file_handle, status=status.HTTP_200_OK, filename=name)
    response['Content-Length'] = file.content.size
    response['X-Content-Check.Sum'] = file.checksum
    response['X-Content-File-Name'] = file.fileName
    response['X-Content-Last-Changed'] = file.last_changed
    response['X-Content-Location'] = file.location
    response['X-Content-Is-Public'] = file.isPublic
    response['Content-Disposition'] = 'attachment; filename="%s"' % file.content.name

    return response


# @api_view(['GET', 'POST'])
# def get_file(request):
#     uid = check_auth(request.GET.get("id_token", ''))
#
#     try:
#         # TODO: CHECK IF IT WORKS
#         file_list = list(request.data['filepath'])
#         filepath = "/" + str(os.sep.join(file_list))
#     except KeyError:
#         return Response({'status': 'missing parameter'}, status=status.HTTP_400_BAD_REQUEST)
#
#     user = CustomUIDModel.objects.filter(uid=uid).get().user
#     try:
#         temp = FileNewModel.objects.get(owner_id=user.pk, content=f'{uid}{filepath}')
#     except ObjectDoesNotExist:
#         return Response({'status': 'Requested file does not exist!'}, status=status.HTTP_404_NOT_FOUND)
#
#     # file = open(f'{settings.MEDIA_ROOT}/{uid}{filepath}', 'r')
#     # TODO: CHECK IF IT WORKS
#     file = open(os.sep.join([settings.MEDIA_ROOT, uid, filepath]), 'r')
#     file.close()
#     filename = os.path.basename(file.name)
#     # print(temp.fileName)
#     json_data = {
#         'fileName': filename,
#         # TODO: CHECK IF IT WORKS
#         'location': file.name.replace(os.sep.join([settings.MEDIA_ROOT, uid]), ''),
#         'content': file.name,
#         'checksum': temp.checksum,
#         'last_changed': temp.last_changed,
#         'isPublic': temp.isPublic,
#     }
#     return Response(data=json_data, status=status.HTTP_200_OK)


@api_view(['POST'])
def upload_file(request):
    # TODO: Abfrage nach verfügbaren Speicherplatz für User
    # TODO: CHECK IF IT WORKS (BEACHTE file_new_location WAR EINMAL file_new.location!!!!!!!!!!!!!)
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
        file_new = FileNewModel()
        file_new.fileName = upload_data['name']
        file_new.location = upload_data['location'].split(';')
        file_new.content = upload
        file_new.checksum = upload_data['checksum']
        file_new.owner = user
    except KeyError:
        return Response({'status': 'missing parameter'}, status=status.HTTP_400_BAD_REQUEST)
    if len(file_new.location) > 0 and file_new.location[0] != '':
        file_new_location = os.sep.join(file_new.location)
    else:
        file_new_location = "/"

    file_name = file_new.content.name.replace(uid, '')

    if file_new_location != 'null':
        file_name = file_name.replace(file_new_location, '')
    file_name = file_name.replace('/', '')

    own_hash = hashlib.sha1(
        str(random.choices(string.ascii_uppercase + string.digits, k=10)).encode("UTF-8")).hexdigest()[
               :5]

    file_name = slugify(file_name)
    if file_new_location != '/':
        temp_loc = '/' + str(file_new_location)
    else:
        temp_loc = '/'
    if FileNewModel.objects.filter(fileName=file_name, location=temp_loc, owner_id=user.pk):
        raw_name = file_name.split('.')
        raw_name[0] = str(raw_name[0]) + '_' + str(own_hash)
        file_name = '.'.join(raw_name)

    if len(file_new_location) > 0:
        file_new.content.name = os.sep.join([str(uid), file_new_location, file_name])
    else:
        file_new.content.name = os.sep.join([str(uid), file_name])

    if file_new_location != '/':
        file_new.location = "/" + str(file_new_location)
    else:
        file_new.location = str(file_new_location)
    file_new.fileName = file_name

    serializer = FileNewSerializer(data=file_new.__dict__)
    if serializer.is_valid():
        file_new.save()
    else:
        # print(serializer.errors)
        # print(file_new.__dict__)
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
        file_name = upload_data['name']
        new_file_name = upload_data['newName']
        location = upload_data['location'].split(';')
    except KeyError:
        return Response({'status': 'missing parameter'}, status=status.HTTP_400_BAD_REQUEST)

    location = os.sep.join(location)
    try:
        file = FileNewModel.objects.get(owner_id=owid, location="/" + str(location), fileName=file_name)
        if FileNewModel.objects.filter(fileName=new_file_name, location="/" + str(location), owner_id=owid).exists():
            raw_name = new_file_name.split('.')
            own_hash = hashlib.sha1(
                str(random.choices(string.ascii_uppercase + string.digits, k=10)).encode("UTF-8")).hexdigest()[
                       :10]
            raw_name[0] = str(raw_name[0]) + str(own_hash)
            new_file_name = slugify('.'.join(raw_name))

    except ObjectDoesNotExist:
        return Response(data={'status': 'File not exist'}, status=status.HTTP_404_NOT_FOUND)

    # path = f'{settings.MEDIA_ROOT}/{uid}{location}{fileName}'
    # new_file_path = f'{settings.MEDIA_ROOT}/{uid}{location}{new_file_name}'
    # TODO: CHECK IF IT WORKS
    path = os.sep.join([settings.MEDIA_ROOT, uid, location, file_name])
    new_file_path = os.sep.join([settings.MEDIA_ROOT, uid, location, new_file_name])
    os.rename(path, new_file_path)
    file.fileName = new_file_name
    file.last_changed = timezone.now()
    if location == '/':
        file.content.name = os.sep.join([str(uid), new_file_name])
    else:
        file.content.name = os.sep.join([str(uid), location, new_file_name])
    file.save()

    return Response(data={'status': 'updated'}, status=status.HTTP_200_OK)


@api_view(['DELETE'])
def delete_file(request):
    uid = check_auth(request.GET.get("id_token", ''))
    try:
        owid = CustomUIDModel.objects.filter(uid=uid).get().user.pk
    except ObjectDoesNotExist:
        return Response({'status': 'User not exist'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        upload_data = request.data
        # TODO Check if it works
        # location = list(upload_data['location'])
        file_list = request.data['location'].split(';')
        # location = '/' + str(os.sep.join(file_list))
        name = upload_data['name']
    except KeyError:
        return Response({'status': 'missing parameter'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        if len(file_list) > 0 and file_list[0] != '':
            current_absolute_location = os.sep.join(file_list)
            file = FileNewModel.objects.get(owner_id=owid, location="/" + str(current_absolute_location), fileName=name)
            os.remove(os.sep.join([settings.MEDIA_ROOT, uid, os.sep.join([current_absolute_location, name])]))
        else:
            file = FileNewModel.objects.get(owner_id=owid, location="/", fileName=name)
            os.remove(os.sep.join([settings.MEDIA_ROOT, uid, name]))
        file.delete()
    except ObjectDoesNotExist:
        return Response(data={'status': 'File not exist'}, status=status.HTTP_404_NOT_FOUND)

    return Response(status=status.HTTP_200_OK)


@api_view(['PUT'])
def move_file(request):
    uid = check_auth(request.GET.get("id_token", ''))
    try:
        owid = CustomUIDModel.objects.filter(uid=uid).get().user.pk
    except ObjectDoesNotExist:
        return Response({'status': 'User not exist'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        upload_data = request.data
        # TODO check if it works
        # location = list(upload_data['location'])
        location_list = request.data['location'].split(';')
        location = str(os.sep.join(location_list))
        newLocation = str(os.sep.join(upload_data['newLocation'].split(';')))
        name = upload_data['name']
    except KeyError:
        return Response({'status': 'missing parameter'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        if len(location_list) > 0 and location_list[0] != '':
            current_absolute_location = location
            file = FileNewModel.objects.get(owner_id=owid, location="/" + str(location), fileName=name)
            if newLocation == '':
                shutil.move(os.sep.join([settings.MEDIA_ROOT, str(uid), current_absolute_location, name]),
                            os.sep.join([settings.MEDIA_ROOT, str(uid), name]))
            else:
                shutil.move(os.sep.join([settings.MEDIA_ROOT, str(uid), current_absolute_location, name]),
                            os.sep.join([settings.MEDIA_ROOT, str(uid), newLocation, name]))
        else:
            file = FileNewModel.objects.get(owner_id=owid, location="/", fileName=name)
            shutil.move(os.sep.join([settings.MEDIA_ROOT, str(uid)]),
                        os.sep.join([settings.MEDIA_ROOT, str(uid), newLocation, name]))

        if newLocation == '':
            file.content.name = os.sep.join([str(uid), name])
            file.location = "/"
        else:
            file.content.name = os.sep.join([str(uid), newLocation, name])
            file.location = "/" + newLocation

        file.save()
    except ObjectDoesNotExist:
        return Response(data={'status': 'File not exist'}, status=status.HTTP_404_NOT_FOUND)
    return Response(status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
def create_directory(request):
    uid = check_auth(request.GET.get("id_token", ''))
    try:
        owid = CustomUIDModel.objects.filter(uid=uid).get().user.pk
    except ObjectDoesNotExist:
        return Response({'status': 'User not exist'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        upload_data = request.data
        # TODO Check if if works
        # location = upload_data['location'].split(';')
        file_list = request.data['location'].split(';')
        location = str(os.sep.join(file_list))
        name = upload_data['name']
    except KeyError:
        return Response({'status': 'missing parameter'}, status=status.HTTP_400_BAD_REQUEST)

    new_dir_path = os.sep.join([settings.MEDIA_ROOT, uid, location, name])

    if not os.path.exists(new_dir_path):
        os.makedirs(new_dir_path)
    else:
        return Response(data={'status': 'directory already exists'}, status=status.HTTP_400_BAD_REQUEST)

    return Response(status=status.HTTP_201_CREATED)


def rename_content_file_directory_in_db(obj: FileNewModel, new_location: str):
    try:
        uid = CustomUIDModel.objects.filter(user_id=obj.owner.id).get().uid
        obj.content.name = os.sep.join([str(uid), new_location, obj.fileName])
        obj.location = "/" + str(os.sep.join([new_location]))
        obj.save()
        return True
    except Exception:
        return False
        # return False


@api_view(['GET', 'POST'])
def rename_directory(request):
    uid = check_auth(request.GET.get("id_token", ''))
    try:
        owid = CustomUIDModel.objects.filter(uid=uid).get().user.pk
    except ObjectDoesNotExist:
        return Response({'status': 'User not exist'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        upload_data = request.data
        location_list = request.data['location'].split(';')
        newLocation = slugify(upload_data['newLocation'])
    except KeyError:
        return Response({'status': 'missing parameter'}, status=status.HTTP_400_BAD_REQUEST)

    current_absolute_location = os.sep.join(location_list)
    path = os.sep.join([settings.MEDIA_ROOT, uid, current_absolute_location])

    location_list[-1] = newLocation
    new_absolute_location = os.sep.join(location_list)
    new_dir_path = os.sep.join([settings.MEDIA_ROOT, uid, new_absolute_location])

    if os.path.exists(path):
        os.rename(path, new_dir_path)
    else:
        return Response(data={'status': 'directory not exists'}, status=status.HTTP_400_BAD_REQUEST)

    rec_list = list(
        FileNewModel.objects.filter(location__startswith="/" + str(current_absolute_location), owner_id=owid))

    try:
        for obj in list(FileNewModel.objects.filter(location__startswith="/" + str(current_absolute_location),
                                                    owner_id=owid)):
            if not rename_content_file_directory_in_db(obj, new_absolute_location):
                raise Exception

    except:
        for obj in rec_list:
            rename_content_file_directory_in_db(obj, obj.location)
        os.rename(new_dir_path, path)
        return Response(status=status.HTTP_400_BAD_REQUEST, data={'status': 'Directory name could not be changed!'})

    return Response(status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
def delete_directory(request):
    uid = check_auth(request.GET.get("id_token", ''))
    try:
        owid = CustomUIDModel.objects.filter(uid=uid).get().user.pk
    except ObjectDoesNotExist:
        return Response({'status': 'User not exist'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        file_list = request.data['location'].split(';')  # ['test']
        location = str(os.sep.join(file_list))  # --> '/test'
        print(location)
        print(file_list)
    except KeyError:
        return Response({'status': 'missing parameter'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        if len(file_list) > 0 and file_list[0] != '':
            file_list = list(FileNewModel.objects.filter(owner_id=owid, location__startswith=location).filter(
                content__contains=location + "/"))
            shutil.rmtree(os.sep.join([settings.MEDIA_ROOT, uid, os.sep.join([location])]))
            print(file_list)
            for file in file_list:
                print(file.fileName)
                file.delete()
        else:
            return Response({'status': 'Parameters are not correct. Please check!'}, status=status.HTTP_400_BAD_REQUEST)
    except ObjectDoesNotExist:
        return Response(data={'status': 'File not exist'}, status=status.HTTP_404_NOT_FOUND)

    return Response(status=status.HTTP_200_OK)
