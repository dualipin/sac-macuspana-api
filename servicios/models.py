from django.db import models
from django_softdelete.models import SoftDeleteModel
from simple_history.models import HistoricalRecords
from core.choices import TipoTramites
from dependencias.models import Dependencia


class TramiteCatalogo(SoftDeleteModel):
    dependencia = models.ForeignKey(
        Dependencia, on_delete=models.CASCADE, related_name="tramites"
    )
    nombre = models.CharField(max_length=255)
    tipo = models.CharField(
        max_length=50, choices=TipoTramites, default=TipoTramites.SOLICITUD_GENERAL
    )
    descripcion = models.TextField()
    imagen = models.ImageField(upload_to="tramites/%Y/%m/%d", blank=True, null=True)
    destacado = models.BooleanField(
        default=False, help_text="Si se debe mostrar en la sección de destacados"
    )
    esta_activo = models.BooleanField(
        default=True, help_text="Indica si el trámite está disponible para solicitar"
    )

    history = HistoricalRecords()


class Requisito(models.Model):
    tramite = models.ForeignKey(
        TramiteCatalogo,
        on_delete=models.CASCADE,
        related_name="requisitos",
        null=True,
        blank=True,
    )
    programa = models.ForeignKey(
        "apoyos.ProgramaSocial",
        on_delete=models.CASCADE,
        related_name="requisitos_especificos",
        null=True,
        blank=True,
    )
    nombre = models.CharField(max_length=255)
    es_obligatorio = models.BooleanField(default=False)
    requiere_documento = models.BooleanField(default=False)
