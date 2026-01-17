from django.urls import path

from ciudadanos.api.views import (
    CiudadanoCreateView, 
    verificar_curp_view,
    CiudadanoListView,
    CiudadanoUpdateView,
    CiudadanoDireccionUpdateView,
)

urlpatterns = [
    path('lista/', CiudadanoListView.as_view(), name='ciudadano-lista'),
    path('actualizar/<int:pk>/', CiudadanoUpdateView.as_view(), name='ciudadano-actualizar'),
    path('actualizar-direccion/', CiudadanoDireccionUpdateView.as_view(), name='ciudadano-direccion-update'),
    path('verificar-curp/', verificar_curp_view, name='ciudadano-verificar-curp'),
    # path('completar-registro/', paso2_registrar_ciudadano, name='ciudadano-completar-registro'),
    path('registrar/', CiudadanoCreateView.as_view(), name='ciudadano-registrar')
]
