from django.db import models


class DirectoryModel(models.Model):
    name = models.CharField(max_length=100)

    def getsize(self, pk):
        "Returns the directory's size"
        result = 0
        for files in FileModel.objects.filter(directory_id=pk):
            result += int(files.size)
        return result


# Model named more precisely to avoid potential overwriting of the built-in File class
class FileModel(models.Model):
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=50)
    location = models.CharField(max_length=1000)
    size = models.IntegerField()
    sizeUnit = models.CharField(max_length=5, default="KB")
    directory = models.ForeignKey(DirectoryModel, on_delete=models.PROTECT)
