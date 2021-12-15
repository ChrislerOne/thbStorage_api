from rest_framework import serializers
from backend.models import FileModel, DirectoryModel, FileNewModel


# class FileSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = FileModel
#         fields = ['name', 'type', 'location', 'size', 'sizeUnit', 'directory', '_data', 'data']

class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileModel
        fields = '__all__'


class FileNewSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileNewModel
        fields = '__all__'


class DirectorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DirectoryModel
        fields = ['name']
