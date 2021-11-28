from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from backend import views

router = routers.SimpleRouter()
router.register(r'files', views.FileViewSet)

urlpatterns = [
    path('', include(router.urls))
]
