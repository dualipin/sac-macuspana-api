from django.db import models


class Localidad(models.Model):
    """
    Modelo Localidad, los datos son los que proporciona el INEGI
    """
    codigo_postal = models.CharField(max_length=5, db_index=True, )
    colonia = models.CharField(max_length=255)
    municipio = models.CharField(max_length=255)
    estado = models.CharField(max_length=100)
    tipo = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.colonia}, {self.municipio}, {self.estado}, CP: {self.codigo_postal}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['codigo_postal', 'colonia', 'municipio', 'estado'],
                name='unique_localidad'
            )
        ]
