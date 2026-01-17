from django.db import models
from django_softdelete.models import SoftDeleteModel
from simple_history.models import HistoricalRecords

from apoyos.models import ProgramaSocial
from ciudadanos.models import Ciudadano
from core.choices import EstatusSolicitud
from core.utils import validar_archivo_documento
from servicios.models import TramiteCatalogo, Requisito


class Solicitud(SoftDeleteModel):
    ciudadano = models.ForeignKey(
        Ciudadano, on_delete=models.CASCADE, related_name="solicitudes"
    )
    tramite_tipo = models.ForeignKey(
        TramiteCatalogo, on_delete=models.PROTECT, related_name="solicitudes"
    )
    programa_social = models.ForeignKey(
        "apoyos.ProgramaSocial",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="solicitudes",
    )
    estatus = models.CharField(
        max_length=25, choices=EstatusSolicitud, default=EstatusSolicitud.PENDIENTE
    )
    descripcion_ciudadano = models.TextField()
    comentarios_revision = models.TextField(
        blank=True, help_text="Comentarios del funcionario durante la revisión"
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    history = HistoricalRecords()

    def verificar_documentacion_completa(self):
        """
        Verifica si todos los requisitos que requieren documentos tienen documentos adjuntos
        """
        # Obtener requisitos del tramite o programa social
        if self.programa_social:
            requisitos = self.programa_social.requisitos_especificos.filter(
                requiere_documento=True
            )
        else:
            requisitos = self.tramite_tipo.requisitos.filter(requiere_documento=True)

        # Si no hay requisitos que requieran documento, la documentación está completa
        if not requisitos.exists():
            return True

        requisitos_ids = set(requisitos.values_list("id", flat=True))
        documentos_ids = set(self.documentos.values_list("requisito_id", flat=True))

        return requisitos_ids == documentos_ids


class DocumentoSolicitud(models.Model):
    solicitud = models.ForeignKey(
        Solicitud, on_delete=models.CASCADE, related_name="documentos"
    )
    requisito = models.ForeignKey(
        Requisito, on_delete=models.PROTECT, related_name="documentos_solicitud"
    )
    archivo = models.FileField(
        upload_to="solicitudes/%Y/%m/%d", validators=[validar_archivo_documento]
    )
    fecha_subida = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        unique_together = ["solicitud", "requisito"]
        ordering = ["fecha_subida"]


class SolicitudAsignacion(models.Model):
    """
    Modelo para gestionar asignaciones de solicitudes a funcionarios.
    Soporta múltiples asignaciones por dependencia.
    """

    solicitud = models.ForeignKey(
        Solicitud, on_delete=models.CASCADE, related_name="asignaciones"
    )
    funcionario = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.CASCADE,
        related_name="solicitudes_asignadas",
    )
    dependencia = models.ForeignKey(
        "dependencias.Dependencia",
        on_delete=models.CASCADE,
        related_name="asignaciones",
    )
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    asignado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        related_name="asignaciones_realizadas",
        help_text="Usuario que realizó la asignación (puede ser automático o manual)",
    )
    es_asignacion_automatica = models.BooleanField(default=False)
    activo = models.BooleanField(
        default=True, help_text="Si la asignación sigue activa o fue reasignada"
    )
    notas = models.TextField(blank=True)

    class Meta:
        ordering = ["-fecha_asignacion"]
        indexes = [
            models.Index(fields=["solicitud", "activo"]),
            models.Index(fields=["funcionario", "activo"]),
        ]
