from django.urls import path, include
from rest_framework import routers
from .views import DependenciaViewSet, FuncionarioViewSet

router = routers.DefaultRouter()
router.register(r'funcionarios', FuncionarioViewSet)
router.register(r'', DependenciaViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
