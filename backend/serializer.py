from rest_framework import serializers
from backend.models import FileNewModel


# class FileSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = FileModel
#         fields = ['name', 'type', 'location', 'size', 'sizeUnit', 'directory', '_data', 'data']

class FileNewSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileNewModel
        fields = '__all__'
