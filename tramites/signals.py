from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from tramites.models import Solicitud, DocumentoSolicitud, SolicitudAsignacion
from notificaciones.services import NotificationManager
from core.choices import EstatusSolicitud


# Instancia global del gestor de notificaciones
notification_manager = NotificationManager()


@receiver(post_save, sender=Solicitud)
def notificar_cambio_estatus_solicitud(sender, instance, created, **kwargs):
    """
    Envía notificación al ciudadano cuando cambia el estatus de su solicitud.
    Utiliza NotificationManager para despacho condicional según rol.
    """
    if created:
        # Notificación al ciudadano de nueva solicitud creada
        notification_manager.notificar_cambio_estado_solicitud(
            solicitud=instance, nuevo_estado=instance.estatus, comentario=None
        )

        # Notificar a funcionarios de la dependencia
        notification_manager.notificar_nueva_solicitud_dependencia(instance)

    else:
        # Verificar si cambió el estatus usando HistoricalRecords
        if hasattr(instance, "history"):
            history = instance.history.all()
            if history.count() > 1:
                ultima_version = history[0]
                version_anterior = history[1]

                if ultima_version.estatus != version_anterior.estatus:
                    # El estatus cambió, enviar notificación al ciudadano
                    notification_manager.notificar_cambio_estado_solicitud(
                        solicitud=instance,
                        nuevo_estado=instance.estatus,
                        comentario=instance.comentarios_revision,
                    )


@receiver(post_save, sender=DocumentoSolicitud)
def notificar_documento_subido(sender, instance, created, **kwargs):
    """
    Notifica cuando se sube un nuevo documento a una solicitud.
    """
    if created:
        # Notificar al ciudadano
        notification_manager.crear_notificacion(
            usuario=instance.solicitud.ciudadano.usuario,
            tipo="DOCUMENTO_RECIBIDO",
            titulo="Documento Recibido",
            mensaje=f"Se ha agregado el documento para el requisito '{instance.requisito.nombre}' a su solicitud.",
            solicitud=instance.solicitud,
            metadata={
                "requisito": instance.requisito.nombre,
                "folio": f"SOL-{instance.solicitud.id:06d}",
            },
        )

        # Notificar a los funcionarios asignados (solo bandeja interna)
        asignaciones_activas = instance.solicitud.asignaciones.filter(activo=True)
        for asignacion in asignaciones_activas:
            notification_manager.crear_notificacion(
                usuario=asignacion.funcionario,
                tipo="DOCUMENTO_RECIBIDO",
                titulo="Nuevo Documento en Solicitud",
                mensaje=f"Se ha agregado un nuevo documento a la solicitud {instance.solicitud.ciudadano.nombre_completo}.",
                solicitud=instance.solicitud,
                metadata={
                    "requisito": instance.requisito.nombre,
                    "folio": f"SOL-{instance.solicitud.id:06d}",
                },
            )


@receiver(post_save, sender=SolicitudAsignacion)
def notificar_asignacion_funcionario(sender, instance, created, **kwargs):
    """
    Notifica al funcionario cuando se le asigna una solicitud.
    Solo bandeja interna (no email).
    """
    if created and instance.activo:
        notification_manager.notificar_asignacion_funcionario(
            funcionario=instance.funcionario, solicitud=instance.solicitud
        )
