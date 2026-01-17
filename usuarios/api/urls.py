from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenBlacklistView
from .views import (
    CustomTokenObtainPairView,
    PerfileView,
    CambiarContrasenaView,
    ActualizarContactoCiudadanoView,
    UsuarioListView,
    CambiarContrasenaAdminView,
    ChangeUserRoleView,
    ChangeUserStatusView,
)

urlpatterns = [
    path('lista/', UsuarioListView.as_view(), name='usuarios-lista'),
    path('cambiar-contrasena/<int:pk>/', CambiarContrasenaAdminView.as_view(), name='usuarios-admin-cambiar-contrasena'),
    path('cambiar-rol/<int:pk>/', ChangeUserRoleView.as_view(), name='usuarios-admin-cambiar-rol'),
    path('cambiar-estatus/<int:pk>/', ChangeUserStatusView.as_view(), name='usuarios-admin-cambiar-estatus'),
    path('iniciar-sesion/', CustomTokenObtainPairView.as_view(), name='usuarios-iniciar-sesion'),
    path('refrescar-token/', TokenRefreshView.as_view(), name='usuarios-refrescar-token'),
    path('cerrar-sesion/', TokenBlacklistView.as_view(), name='usuarios-cerrar-sesion'),
    path('perfil/', PerfileView.as_view(), name='usuarios-perfil'),
    path('cambiar-contrasena/', CambiarContrasenaView.as_view(), name='usuarios-cambiar-contrasena'),
    path('actualizar-contacto/', ActualizarContactoCiudadanoView.as_view(), name='usuarios-actualizar-contacto'),
]
