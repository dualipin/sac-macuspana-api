from django.db import models
from dependencias.models import Dependencia


class ProgramaSocial(models.Model):
    dependencia = models.ForeignKey(Dependencia, on_delete=models.CASCADE, related_name="programas_sociales")
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    imagen = models.ImageField(upload_to="programas/%Y/%m/%d", blank=True, null=True)
    destacado = models.BooleanField(default=False, help_text="Si se debe mostrar en la sección de destacados")
    categoria = models.CharField(max_length=100, blank=True, help_text="Categoría del programa (ej: Bienestar Social, Educación)")
    esta_activo = models.BooleanField(default=True)
