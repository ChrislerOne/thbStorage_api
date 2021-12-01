from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from rest_framework.authtoken import views as v
from backend import views

router = routers.SimpleRouter()
router.register(r'files', views.FileViewSet)
# TODO authentication router

urlpatterns = [
    path('', include(router.urls)),
    # API-Endpoint to obtain user token with cred
    path('api-token-auth/', v.obtain_auth_token)

]
