from django.urls import path
from .views import NotificacionView

urlpatterns = [
    path('', NotificacionView.as_view(), name='notificaciones-list')
]