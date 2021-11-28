from django.contrib.auth.models import User
from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from backend.serializer import FileSerializer
from backend.models import FileModel, DirectoryModel
from django.core.files.storage import FileSystemStorage


# Create your views here.
class FileViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows files to be viewed or edited
    """
    queryset = FileModel.objects.all()
    serializer_class = FileSerializer
    parser_class = (MultiPartParser,)

    def perform_create(self, serializer):
        upload = self.request.FILES['content']
        upload_data = self.request.data

        directory = DirectoryModel.objects.get(pk=1)
        user = User.objects.get(pk=1)

        file = FileModel()
        file.name = upload_data['name']
        file.location = upload_data['location']
        file.content = upload
        file.checksum = ''
        # TODO: get directory of user and match it with request
        file.directory = directory
        # TODO: Users Account erhalten und dementsprechend eintragen
        file.owner = user
        if file.location != 'null':
            file.content.name = str(user.get_username()) + '/' + file.location + '/' + file.name
        else:
            file.content.name = str(user.get_username()) + '/' + file.name

        serializer = FileSerializer(data=file.__dict__)
        if serializer.is_valid():
            serializer.save()
        else:
            print(serializer.errors)
            print(file.__dict__)
            return Response(serializer.errors, status=400)

        return Response(status=204)
