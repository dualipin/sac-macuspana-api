from django.db import models

from usuarios.models import Usuario


class TipoNotificacion(models.TextChoices):
    """Tipos de notificaciones del sistema"""

    SOLICITUD_CREADA = "SOLICITUD_CREADA", "Solicitud Creada"
    SOLICITUD_ACTUALIZADA = "SOLICITUD_ACTUALIZADA", "Solicitud Actualizada"
    SOLICITUD_EN_REVISION = "SOLICITUD_EN_REVISION", "Solicitud en Revisión"
    SOLICITUD_REQUIERE_INFO = "SOLICITUD_REQUIERE_INFO", "Requiere Información"
    SOLICITUD_APROBADA = "SOLICITUD_APROBADA", "Solicitud Aprobada"
    SOLICITUD_RECHAZADA = "SOLICITUD_RECHAZADA", "Solicitud Rechazada"
    SOLICITUD_ASIGNADA = "SOLICITUD_ASIGNADA", "Solicitud Asignada"
    DOCUMENTO_RECIBIDO = "DOCUMENTO_RECIBIDO", "Documento Recibido"
    SISTEMA = "SISTEMA", "Notificación del Sistema"


class Notificacion(models.Model):
    usuario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name="notificaciones"
    )
    tipo = models.CharField(
        max_length=50,
        choices=TipoNotificacion.choices,
        default=TipoNotificacion.SISTEMA,
    )
    titulo = models.CharField(max_length=255)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_lectura = models.DateTimeField(null=True, blank=True)

    # Referencia a la solicitud (si aplica)
    referencia_solicitud = models.ForeignKey(
        "tramites.Solicitud",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notificaciones",
    )

    # Metadata adicional (JSON para flexibilidad)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Datos adicionales como folio, dependencia, etc.",
    )

    # Control de envío de email
    email_enviado = models.BooleanField(
        default=False, help_text="Indica si se envió notificación por correo"
    )
    requiere_email = models.BooleanField(
        default=False,
        help_text="Indica si debe enviarse email (depende del rol del usuario)",
    )

    class Meta:
        ordering = ["-fecha_creacion"]
        indexes = [
            models.Index(fields=["usuario", "-fecha_creacion"]),
            models.Index(fields=["usuario", "leida"]),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.usuario.username}"
