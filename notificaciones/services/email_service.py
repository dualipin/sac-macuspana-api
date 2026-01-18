"""
Servicio para envío de correos electrónicos.
Utiliza el sistema de email de Django.
"""

from typing import Dict, Any
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string


class EmailService:
    """Servicio para gestión de envío de emails."""

    def __init__(self):
        self.from_email = getattr(
            settings, "DEFAULT_FROM_EMAIL", "noreply@macuspana.gob.mx"
        )

    def enviar_notificacion(
        self,
        destinatario: str,
        asunto: str,
        mensaje: str,
        metadata: Dict[str, Any] = None,
    ) -> bool:
        """
        Envía un email de notificación.

        Args:
            destinatario: Email del destinatario
            asunto: Asunto del correo
            mensaje: Mensaje principal
            metadata: Datos adicionales para el template

        Returns:
            True si se envió exitosamente, False en caso contrario
        """
        try:
            # Preparar contexto para el template
            contexto = {
                "asunto": asunto,
                "mensaje": mensaje,
                "metadata": metadata or {},
            }

            # Renderizar template HTML (si existe)
            try:
                html_message = render_to_string(
                    "notificaciones/email_notificacion.html", contexto
                )
            except Exception:
                # Si no existe template, usar mensaje plano
                html_message = None

            # Enviar email
            send_mail(
                subject=asunto,
                message=mensaje,
                from_email=self.from_email,
                recipient_list=[destinatario],
                html_message=html_message,
                fail_silently=False,
            )

            return True

        except Exception as e:
            print(f"Error enviando email a {destinatario}: {e}")
            return False

    def enviar_cambio_estado_solicitud(
        self,
        destinatario: str,
        folio: str,
        tramite: str,
        nuevo_estado: str,
        comentario: str = None,
    ) -> bool:
        """
        Envía notificación de cambio de estado de solicitud.
        """
        asunto = f"Actualización de Solicitud {folio}"

        mensaje = f"""
Estimado ciudadano,

Le informamos que su solicitud {folio} de {tramite} ha sido actualizada.

Estado actual: {nuevo_estado}
"""

        if comentario:
            mensaje += f"\nComentario: {comentario}\n"

        mensaje += """
Puede consultar el detalle de su solicitud ingresando al portal:
{portal_url}

Atentamente,
H. Ayuntamiento de Macuspana
""".format(
            portal_url=getattr(
                settings, "PORTAL_URL", "https://portal.macuspana.gob.mx"
            )
        )

        metadata = {
            "folio": folio,
            "tramite": tramite,
            "estado": nuevo_estado,
            "comentario": comentario,
        }

        return self.enviar_notificacion(
            destinatario=destinatario, asunto=asunto, mensaje=mensaje, metadata=metadata
        )
