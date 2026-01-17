from django.urls import path, include
from rest_framework import routers

from .views import TramiteCatalogoViewSet, RequisitoViewSet

router = routers.DefaultRouter()
router.register("catalogo", TramiteCatalogoViewSet)
router.register("requisitos", RequisitoViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
