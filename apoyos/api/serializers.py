from rest_framework import serializers
from apoyos.models import ProgramaSocial
from servicios.api.serializers import RequisitoSerializer


class ProgramaSocialSerializer(serializers.ModelSerializer):
    requisitos_especificos = RequisitoSerializer(many=True, read_only=True)

    class Meta:
        model = ProgramaSocial
        fields = [
            "id",
            "dependencia",
            "nombre",
            "descripcion",
            "esta_activo",
            "requisitos_especificos",
            "imagen",
            "destacado",
            "categoria",
        ]
        read_only_fields = ["id"]


class ProgramaSocialCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear/actualizar programas sin requisitos anidados
    Los requisitos se gestionan por separado
    """

    class Meta:
        model = ProgramaSocial
        fields = ["id", "dependencia", "nombre", "descripcion", "esta_activo", "imagen", "destacado", "categoria"]
        read_only_fields = ["id"]


class ProgramaSocialListSerializer(serializers.ModelSerializer):
    """
    Serializer ligero para listados sin incluir todos los requisitos
    """

    cantidad_requisitos = serializers.SerializerMethodField()
    nombre_dependencia = serializers.CharField(
        source="dependencia.nombre", read_only=True
    )

    class Meta:
        model = ProgramaSocial
        fields = [
            "id",
            "nombre",
            "descripcion",
            "esta_activo",
            "nombre_dependencia",
            "cantidad_requisitos",
            "imagen",
            "destacado",
            "categoria",
        ]
        read_only_fields = ["id"]

    def get_cantidad_requisitos(self, obj):
        return obj.requisitos_especificos.count()
