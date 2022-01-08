from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from rest_framework.authtoken import views as v
from backend import views

router = routers.SimpleRouter()
# router.register(r'files', views.FileViewSet)
# TODO authentication router

urlpatterns = [
    path('', include(router.urls)),
    path('files/', views.files_list),
    path('files/bypath', views.files_list_by_path),
    path('file/upload', views.upload_file),
    path('file', views.get_file),
    path('file/specific', views.get_specific_file),
    path('filename/update', views.rename_filename),
    path('file/delete', views.delete_file),
    path('directory/create', views.create_directory),
    path('directory/update', views.rename_directory),
    # API-Endpoint to obtain user token with cred
    path('api-token-auth/', v.obtain_auth_token)

]
