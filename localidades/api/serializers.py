from rest_framework import serializers

from localidades.models import Localidad


class LocalidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Localidad
        fields = '__all__'
