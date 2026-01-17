from django.db import models
from django_softdelete.models import SoftDeleteModel
from simple_history.models import HistoricalRecords

from core.choices import Generos, TipoDependencia
from usuarios.models import Usuario


class Dependencia(SoftDeleteModel):
    nombre = models.CharField(max_length=255)
    siglas = models.CharField(max_length=15, blank=True, null=True)
    tipo = models.CharField(max_length=20, choices=TipoDependencia, default=TipoDependencia.DEPARTAMENTO)
    representante = models.OneToOneField(
        'dependencias.Funcionario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dependencia_titular'
    )

    history = HistoricalRecords()


class Funcionario(SoftDeleteModel):
    nombre_completo = models.CharField(max_length=255)
    correo = models.EmailField()
    telefono = models.CharField(max_length=15, blank=True, null=True)
    cargo = models.CharField(max_length=100)
    sexo = models.CharField(max_length=1, choices=Generos, default=Generos.OTRO)
    dependencia = models.ForeignKey(
        Dependencia,
        on_delete=models.PROTECT,
        related_name='personal'
    )

    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='funcionario')

    history = HistoricalRecords()
