from django.db.models.signals import post_save
from django.dispatch import receiver
from tramites.models import Solicitud
from notificaciones.models import Notificacion
from core.choices import EstatusSolicitud


@receiver(post_save, sender=Solicitud)
def notificar_cambio_estatus_solicitud(sender, instance, created, **kwargs):
    """
    Envía notificación al ciudadano cuando cambia el estatus de su solicitud
    """
    if created:
        # Notificación de nueva solicitud creada
        Notificacion.objects.create(
            usuario=instance.ciudadano.usuario,
            titulo="Solicitud Recibida",
            mensaje=f"Su solicitud para '{instance.tramite_tipo.nombre}' ha sido recibida y está en proceso de revisión.",
        )
    else:
        # Verificar si cambió el estatus
        # Para detectar cambios, necesitamos comparar con la versión anterior
        # Usaremos HistoricalRecords que ya está configurado

        if hasattr(instance, "history"):
            history = instance.history.all()
            if history.count() > 1:
                ultima_version = history[0]
                version_anterior = history[1]

                if ultima_version.estatus != version_anterior.estatus:
                    # El estatus cambió, enviar notificación
                    mensajes = {
                        EstatusSolicitud.EN_REVISION: f"Su solicitud está en revisión por parte de nuestro equipo.",
                        EstatusSolicitud.REQUIERE_INFORMACION: f"Su solicitud requiere información adicional. Por favor revise los comentarios.",
                        EstatusSolicitud.APROBADO: f"¡Felicidades! Su solicitud ha sido aprobada.",
                        EstatusSolicitud.ACEPTADO: f"Su solicitud ha sido aceptada y está siendo procesada.",
                        EstatusSolicitud.RECHAZADO: f"Lamentablemente su solicitud ha sido rechazada. Revise los comentarios para más detalles.",
                    }

                    mensaje_base = mensajes.get(
                        instance.estatus,
                        f"El estatus de su solicitud ha cambiado a: {instance.get_estatus_display()}",
                    )

                    if instance.comentarios_revision:
                        mensaje_completo = f"{mensaje_base}\n\nComentarios: {instance.comentarios_revision}"
                    else:
                        mensaje_completo = mensaje_base

                    Notificacion.objects.create(
                        usuario=instance.ciudadano.usuario,
                        titulo=f"Actualización de Solicitud - {instance.get_estatus_display()}",
                        mensaje=mensaje_completo,
                    )


# Opcional: Notificación cuando se sube un documento
from tramites.models import DocumentoSolicitud


@receiver(post_save, sender=DocumentoSolicitud)
def notificar_documento_subido(sender, instance, created, **kwargs):
    """
    Notifica cuando se sube un nuevo documento a una solicitud
    """
    if created:
        # Notificar al ciudadano
        Notificacion.objects.create(
            usuario=instance.solicitud.ciudadano.usuario,
            titulo="Documento Agregado",
            mensaje=f"Se ha agregado el documento para el requisito '{instance.requisito.nombre}' a su solicitud.",
        )

        # También podríamos notificar a los funcionarios asignados
        asignaciones_activas = instance.solicitud.asignaciones.filter(activo=True)
        for asignacion in asignaciones_activas:
            Notificacion.objects.create(
                usuario=asignacion.funcionario,
                titulo="Nuevo Documento en Solicitud",
                mensaje=f"Se ha agregado un nuevo documento a la solicitud de {instance.solicitud.ciudadano.nombre}.",
            )
