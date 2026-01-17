import hashlib

from django.db import models
from django_softdelete.models import SoftDeleteModel
from encrypted_model_fields.fields import EncryptedCharField, EncryptedDateField, EncryptedEmailField
from simple_history.models import HistoricalRecords
from core.choices import Generos
from localidades.models import Localidad
from usuarios.models import Usuario


class Ciudadano(SoftDeleteModel):
    # Campos personales
    curp = EncryptedCharField(max_length=18)
    curp_hash = models.CharField(max_length=64, unique=True, db_index=True, default=None)  # Hash para búsquedas
    nombre = models.CharField(max_length=200)
    apellido_paterno = models.CharField(max_length=200)
    apellido_materno = models.CharField(max_length=200, blank=True, null=True)
    fecha_nacimiento = EncryptedDateField()
    sexo = models.CharField(
        max_length=1,
        choices=Generos,
        default=Generos.OTRO,
    )

    # Información de contacto
    correo = EncryptedEmailField()
    correo_hash = models.CharField(max_length=64, unique=True, db_index=True, default=None, null=True, blank=True)
    telefono = EncryptedCharField(max_length=15)

    # Dirección
    calle = EncryptedCharField(max_length=200)
    numero_exterior = EncryptedCharField(max_length=10)
    numero_interior = models.CharField(max_length=10, blank=True, null=True)
    localidad = models.ForeignKey(
        Localidad, on_delete=models.SET_NULL, related_name="ciudadanos", null=True
    )

    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name="ciudadano")

    history = HistoricalRecords()

    @property
    def nombre_completo(self):
        if self.apellido_materno:
            return f"{self.nombre} {self.apellido_paterno} {self.apellido_materno}"
        return f"{self.nombre} {self.apellido_paterno}"

    @property
    def direccion_completa(self):
        if not self.numero_interior:
            return f"{self.calle}, {self.numero_exterior}, {self.localidad}"
        return f"{self.calle}, {self.numero_exterior}, {self.numero_interior}, {self.localidad}"

    def save(self, *args, **kwargs):
        # Generar hash automáticamente antes de guardar
        if self.curp:
            self.curp_hash = hashlib.sha256(self.curp.upper().encode()).hexdigest()
        if self.correo:
            self.correo_hash = hashlib.sha256(self.correo.lower().encode()).hexdigest()
        super().save(*args, **kwargs)
