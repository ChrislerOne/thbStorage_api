from django.shortcuts import render
from backend.models import FileModel, DirectoryModel


# Create your views here.

def test(request):
    directory = DirectoryModel(name="test")
    directory.save()
    did = directory.id

    file1 = FileModel(name="file1", type=".pdf", location="C:/", size=31, directory_id=did)
    file2 = FileModel(name="file2", type=".pdf", location="C:/", size=23, directory_id=did)
    file3 = FileModel(name="file3", type=".pdf", location="C:/", size=15, directory_id=did)
    file4 = FileModel(name="file4", type=".pdf", location="C:/", size=309, directory_id=did)

    file1.save()
    file2.save()
    file3.save()
    file4.save()

    print(DirectoryModel.getsize(directory, did))

    return render(request, 'index.html')
