from rest_framework import serializers
from backend.models import FileModel, DirectoryModel


# class FileSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = FileModel
#         fields = ['name', 'type', 'location', 'size', 'sizeUnit', 'directory', '_data', 'data']

class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileModel
        fields = ['content', 'name', 'location']


class DirectorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DirectoryModel
        fields = ['name']
