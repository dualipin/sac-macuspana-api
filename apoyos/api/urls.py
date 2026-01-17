from django.urls import path, include
from rest_framework import routers

from .views import ProgramaSocialViewSet

router = routers.DefaultRouter()
router.register("programas", ProgramaSocialViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
