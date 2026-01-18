"""
Comando para crear notificaciones de prueba
"""

from django.core.management.base import BaseCommand
from usuarios.models import Usuario
from notificaciones.services import NotificationManager
from notificaciones.models import TipoNotificacion


class Command(BaseCommand):
    help = "Crea notificaciones de prueba para el primer usuario"

    def handle(self, *args, **options):
        # Obtener el primer usuario
        usuario = Usuario.objects.first()

        if not usuario:
            self.stdout.write(self.style.ERROR("No hay usuarios en el sistema"))
            return

        self.stdout.write(f"Creando notificaciones para: {usuario.username}")

        # Crear notificación manager
        manager = NotificationManager()

        # Crear varias notificaciones de prueba
        notificaciones = [
            {
                "tipo": TipoNotificacion.SOLICITUD_CREADA,
                "titulo": "Solicitud Recibida",
                "mensaje": "Tu solicitud ha sido recibida y está en proceso de revisión.",
            },
            {
                "tipo": TipoNotificacion.SOLICITUD_EN_REVISION,
                "titulo": "Solicitud en Revisión",
                "mensaje": "Tu solicitud está siendo revisada por nuestro equipo.",
            },
            {
                "tipo": TipoNotificacion.SOLICITUD_APROBADA,
                "titulo": "Solicitud Aprobada",
                "mensaje": "¡Felicidades! Tu solicitud ha sido aprobada.",
            },
        ]

        for notif_data in notificaciones:
            notif = manager.crear_notificacion(usuario=usuario, **notif_data)
            self.stdout.write(self.style.SUCCESS(f"✓ Creada: {notif.titulo}"))

        # Mostrar estadísticas
        total = usuario.notificaciones.count()
        no_leidas = usuario.notificaciones.filter(leida=False).count()

        self.stdout.write(self.style.SUCCESS(f"\n✓ Total de notificaciones: {total}"))
        self.stdout.write(self.style.SUCCESS(f"✓ No leídas: {no_leidas}"))
