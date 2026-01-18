from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.utils import timezone

from notificaciones.models import Notificacion
from notificaciones.services import NotificationManager
from .serializers import NotificacionSerializer, NotificacionListSerializer


class NotificacionListView(generics.ListAPIView):
    """Lista todas las notificaciones del usuario autenticado."""

    permission_classes = [IsAuthenticated]
    serializer_class = NotificacionSerializer

    def get_queryset(self):
        user = self.request.user
        return Notificacion.objects.filter(usuario=user).select_related(
            "referencia_solicitud", "usuario"
        )


class NotificacionNoLeidasView(generics.ListAPIView):
    """Lista solo las notificaciones no leídas."""

    permission_classes = [IsAuthenticated]
    serializer_class = NotificacionSerializer

    def get_queryset(self):
        user = self.request.user
        return Notificacion.objects.filter(usuario=user, leida=False).select_related(
            "referencia_solicitud", "usuario"
        )


class NotificacionNoLeidasCountView(APIView):
    """Obtiene el conteo de notificaciones no leídas."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        conteo = Notificacion.objects.filter(usuario=user, leida=False).count()

        return Response({"no_leidas": conteo})


class NotificacionMarcarLeidaView(APIView):
    """Marca una notificación como leída."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            notificacion = Notificacion.objects.get(pk=pk, usuario=request.user)

            notification_manager = NotificationManager()
            notification_manager.marcar_como_leida(notificacion)

            serializer = NotificacionSerializer(notificacion)
            return Response(serializer.data)

        except Notificacion.DoesNotExist:
            return Response(
                {"error": "Notificación no encontrada"},
                status=status.HTTP_404_NOT_FOUND,
            )


class NotificacionMarcarTodasLeidasView(APIView):
    """Marca todas las notificaciones del usuario como leídas."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        notification_manager = NotificationManager()
        cantidad = notification_manager.marcar_todas_como_leidas(request.user)

        return Response(
            {
                "detail": f"{cantidad} notificaciones marcadas como leídas",
                "cantidad": cantidad,
            }
        )
