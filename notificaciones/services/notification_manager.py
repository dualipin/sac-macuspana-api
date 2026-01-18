"""
Servicio centralizado para gestión de notificaciones.
Maneja la lógica de despacho condicional según el rol del usuario.
"""

from typing import Optional, Dict, Any
from django.utils import timezone

from core.choices import Roles
from notificaciones.models import Notificacion, TipoNotificacion
from tramites.models import Solicitud
from usuarios.models import Usuario
from .email_service import EmailService


class NotificationManager:
    """
    Gestor central de notificaciones del sistema.

    Reglas de negocio:
    - Ciudadanos: Persistir en DB + Enviar email
    - Funcionarios/Administradores: Solo persistir en DB (bandeja interna)
    """

    def __init__(self):
        self.email_service = EmailService()

    def crear_notificacion(
        self,
        usuario: Usuario,
        tipo: str,
        titulo: str,
        mensaje: str,
        solicitud: Optional[Solicitud] = None,
        metadata: Optional[Dict[str, Any]] = None,
        forzar_sin_email: bool = False,
    ) -> Notificacion:
        """
        Crea una notificación y determina si debe enviarse por email según el rol.

        Args:
            usuario: Usuario destinatario
            tipo: Tipo de notificación (usar TipoNotificacion)
            titulo: Título de la notificación
            mensaje: Mensaje descriptivo
            solicitud: Referencia a la solicitud (opcional)
            metadata: Datos adicionales (opcional)
            forzar_sin_email: Si True, no envía email aunque sea ciudadano (opcional)

        Returns:
            Instancia de Notificacion creada
        """
        # Determinar si requiere email según el rol y parámetro
        requiere_email = usuario.rol == Roles.CIUDADANO and not forzar_sin_email

        # Crear notificación en base de datos
        notificacion = Notificacion.objects.create(
            usuario=usuario,
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            referencia_solicitud=solicitud,
            metadata=metadata or {},
            requiere_email=requiere_email,
            email_enviado=False,
        )

        # Si es ciudadano y no se fuerza sin email, enviar email
        if requiere_email:
            self._enviar_email_async(notificacion)

        return notificacion

    def _enviar_email_async(self, notificacion: Notificacion) -> None:
        """
        Envía el email de notificación de forma asíncrona.
        Actualiza el estado email_enviado.
        """
        try:
            # Obtener email del ciudadano
            if hasattr(notificacion.usuario, "ciudadano"):
                email_destino = str(notificacion.usuario.ciudadano.correo)

                # Enviar email
                self.email_service.enviar_notificacion(
                    destinatario=email_destino,
                    asunto=notificacion.titulo,
                    mensaje=notificacion.mensaje,
                    metadata=notificacion.metadata,
                )

                # Marcar como enviado
                notificacion.email_enviado = True
                notificacion.save(update_fields=["email_enviado"])
        except Exception as e:
            # Log del error pero no falla la creación de la notificación
            print(f"Error enviando email para notificación {notificacion.id}: {e}")

    def notificar_cambio_estado_solicitud(
        self, solicitud: Solicitud, nuevo_estado: str, comentario: Optional[str] = None
    ) -> Notificacion:
        """
        Notifica al ciudadano sobre cambios en el estado de su solicitud.
        """
        # Mapeo de estados a tipos de notificación
        estado_to_tipo = {
            "PENDIENTE": TipoNotificacion.SOLICITUD_CREADA,
            "EN_REVISION": TipoNotificacion.SOLICITUD_EN_REVISION,
            "REQUIERE_INFORMACION": TipoNotificacion.SOLICITUD_REQUIERE_INFO,
            "APROBADO": TipoNotificacion.SOLICITUD_APROBADA,
            "RECHAZADO": TipoNotificacion.SOLICITUD_RECHAZADA,
        }

        tipo = estado_to_tipo.get(nuevo_estado, TipoNotificacion.SOLICITUD_ACTUALIZADA)

        # Obtener usuario del ciudadano
        usuario = solicitud.ciudadano.usuario

        # Generar folio para metadata
        folio = f"SOL-{solicitud.id:06d}"

        # Determinar si es programa social o trámite
        if solicitud.programa_social:
            nombre_servicio = solicitud.programa_social.nombre
            tipo_servicio = "Programa Social"
        else:
            nombre_servicio = solicitud.tramite_tipo.nombre
            tipo_servicio = "Trámite"

        # Construir título y mensaje
        titulo = f"Actualización de Solicitud {folio}"
        mensaje = self._generar_mensaje_estado(nuevo_estado, solicitud, comentario)

        metadata = {
            "solicitud_id": solicitud.id,
            "folio": folio,
            "tramite": nombre_servicio,
            "tipo_servicio": tipo_servicio,
            "estado_anterior": solicitud.estatus,
            "estado_nuevo": nuevo_estado,
        }

        if comentario:
            metadata["comentario"] = comentario

        return self.crear_notificacion(
            usuario=usuario,
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            solicitud=solicitud,
            metadata=metadata,
        )

    def notificar_asignacion_funcionario(
        self, funcionario: Usuario, solicitud: Solicitud
    ) -> Notificacion:
        """
        Notifica a un funcionario que se le ha asignado una solicitud.
        Solo bandeja interna (no email).
        """
        folio = f"SOL-{solicitud.id:06d}"

        # Determinar si es programa social o trámite
        if solicitud.programa_social:
            nombre_servicio = solicitud.programa_social.nombre
        else:
            nombre_servicio = solicitud.tramite_tipo.nombre

        titulo = f"Nueva Solicitud Asignada: {folio}"
        mensaje = (
            f"Se te ha asignado la solicitud {folio} - {nombre_servicio}. "
            f"Ciudadano: {solicitud.ciudadano.nombre_completo}."
        )

        metadata = {
            "solicitud_id": solicitud.id,
            "folio": folio,
            "tramite": nombre_servicio,
            "ciudadano": solicitud.ciudadano.nombre_completo,
            "dependencia": (
                solicitud.dependencia_actual().nombre
                if solicitud.dependencia_actual()
                else "N/A"
            ),
        }

        return self.crear_notificacion(
            usuario=funcionario,
            tipo=TipoNotificacion.SOLICITUD_ASIGNADA,
            titulo=titulo,
            mensaje=mensaje,
            solicitud=solicitud,
            metadata=metadata,
        )

    def notificar_nueva_solicitud_dependencia(
        self, solicitud: Solicitud
    ) -> list[Notificacion]:
        """
        Notifica a los funcionarios de una dependencia sobre una nueva solicitud.
        Solo bandeja interna (no email).
        """
        notificaciones = []
        dependencia = solicitud.dependencia_actual()

        if not dependencia:
            return notificaciones

        # Obtener funcionarios de la dependencia
        funcionarios = Usuario.objects.filter(
            funcionario__dependencia=dependencia,
            rol__in=[Roles.FUNCIONARIO, Roles.ADMINISTRADOR],
        )

        folio = f"SOL-{solicitud.id:06d}"

        # Determinar si es programa social o trámite
        if solicitud.programa_social:
            nombre_servicio = solicitud.programa_social.nombre
        else:
            nombre_servicio = solicitud.tramite_tipo.nombre

        for funcionario in funcionarios:
            titulo = f"Nueva Solicitud Recibida: {folio}"
            mensaje = (
                f"Nueva solicitud {folio} - {nombre_servicio} "
                f"de {solicitud.ciudadano.nombre_completo}."
            )

            metadata = {
                "solicitud_id": solicitud.id,
                "folio": folio,
                "tramite": nombre_servicio,
                "ciudadano": solicitud.ciudadano.nombre_completo,
                "dependencia": dependencia.nombre,
            }

            notif = self.crear_notificacion(
                usuario=funcionario,
                tipo=TipoNotificacion.SOLICITUD_CREADA,
                titulo=titulo,
                mensaje=mensaje,
                solicitud=solicitud,
                metadata=metadata,
            )
            notificaciones.append(notif)

        return notificaciones

    def marcar_como_leida(self, notificacion: Notificacion) -> None:
        """Marca una notificación como leída."""
        if not notificacion.leida:
            notificacion.leida = True
            notificacion.fecha_lectura = timezone.now()
            notificacion.save(update_fields=["leida", "fecha_lectura"])

    def marcar_todas_como_leidas(self, usuario: Usuario) -> int:
        """Marca todas las notificaciones de un usuario como leídas."""
        return Notificacion.objects.filter(usuario=usuario, leida=False).update(
            leida=True, fecha_lectura=timezone.now()
        )

    def _generar_mensaje_estado(
        self, estado: str, solicitud: Solicitud, comentario: Optional[str] = None
    ) -> str:
        """Genera mensaje personalizado según el estado."""
        folio = f"SOL-{solicitud.id:06d}"

        # Determinar si es programa social o trámite
        if solicitud.programa_social:
            nombre_servicio = solicitud.programa_social.nombre
        else:
            nombre_servicio = solicitud.tramite_tipo.nombre

        mensajes = {
            "PENDIENTE": f"Tu solicitud {folio} de {nombre_servicio} ha sido recibida y está en espera de revisión.",
            "EN_REVISION": f"Tu solicitud {folio} de {nombre_servicio} está siendo revisada por la dependencia correspondiente.",
            "REQUIERE_INFORMACION": f"Tu solicitud {folio} de {nombre_servicio} requiere información adicional.",
            "APROBADO": f"¡Felicidades! Tu solicitud {folio} de {nombre_servicio} ha sido aprobada.",
            "RECHAZADO": f"Tu solicitud {folio} de {nombre_servicio} ha sido rechazada.",
        }

        mensaje_base = mensajes.get(
            estado, f"Tu solicitud {folio} ha sido actualizada."
        )

        if comentario:
            mensaje_base += f" Comentario: {comentario}"

        return mensaje_base
