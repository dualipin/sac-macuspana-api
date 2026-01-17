from rest_framework.response import Response
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from notificaciones.models import Notificacion
from .serializers import NotificacionSerializer

class NotificacionView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificacionSerializer

    def get_queryset(self):
        user = self.request.user
        return Notificacion.objects.filter(usuario=user).order_by('-fecha_creacion')

