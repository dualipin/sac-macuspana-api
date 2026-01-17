from django.db import models


class Generos(models.TextChoices):
    MASCULINO = "M", "Masculino"
    FEMENINO = "F", "Femenino"
    OTRO = "O", "Otro"


class Roles(models.TextChoices):
    ADMINISTRADOR = "ADMINISTRADOR", "Administrador"
    FUNCIONARIO = "FUNCIONARIO", "Funcionario Publico"
    CIUDADANO = "CIUDADANO", "Ciudadano"


class TipoTramites(models.TextChoices):
    SOLICITUD_GENERAL = "SOLICITUD_GENERAL", "Solicitud General"
    TRAMITE_ADMINISTRATIVO = "TRAMITE_ADMINISTRATIVO", "Tramite Administrativo"
    APOYO_SOCIAL = "APOYO_SOCIAL", "Apoyo Social"


class EstatusSolicitud(models.TextChoices):
    PENDIENTE = "PENDIENTE", "Pendiente"
    EN_REVISION = "EN_REVISION", "En Revisión"
    REQUIERE_INFORMACION = "REQUIERE_INFORMACION", "Requiere Información"
    APROBADO = "APROBADO", "Aprobado"
    ACEPTADO = "ACEPTADO", "Aceptado"
    RECHAZADO = "RECHAZADO", "Rechazado"


class TipoDependencia(models.TextChoices):
    COORDINACION = "coordinación", "Coordinación"
    DIRECCION = "dirección", "Dirección"
    SUBDIRECCION = "subdirección", "Subdirección"
    DEPARTAMENTO = "departamento", "Departamento"
    OTROS = "otros", "Otros"
