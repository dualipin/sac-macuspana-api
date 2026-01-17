from rest_framework import serializers

from servicios.models import TramiteCatalogo, Requisito


class RequisitoSerializer(serializers.ModelSerializer):
    """
    Serializer para gestionar requisitos de trámites y programas sociales
    """

    class Meta:
        model = Requisito
        fields = [
            "id",
            "tramite",
            "programa",
            "nombre",
            "es_obligatorio",
            "requiere_documento",
        ]
        read_only_fields = ["id"]

    def validate(self, data):
        """
        Validar que el requisito esté asociado a un trámite O programa, no ambos
        """
        tramite = data.get("tramite")
        programa = data.get("programa")

        if tramite and programa:
            raise serializers.ValidationError(
                "Un requisito no puede estar asociado tanto a un trámite como a un programa"
            )

        if not tramite and not programa:
            raise serializers.ValidationError(
                "Un requisito debe estar asociado a un trámite o a un programa"
            )

        return data


class RequisitoCreateSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para crear requisitos
    """

    class Meta:
        model = Requisito
        fields = [
            "tramite",
            "programa",
            "nombre",
            "es_obligatorio",
            "requiere_documento",
        ]


class TramiteCatalogoSerializer(serializers.ModelSerializer):
    requisitos = RequisitoSerializer(many=True, read_only=True)
    nombre_dependencia = serializers.CharField(
        source="dependencia.nombre", read_only=True, allow_null=True
    )
    cantidad_requisitos = serializers.SerializerMethodField()

    class Meta:
        model = TramiteCatalogo
        fields = [
            "id",
            "nombre",
            "tipo",
            "descripcion",
            "imagen",
            "dependencia",
            "nombre_dependencia",
            "requisitos",
            "cantidad_requisitos",
            "destacado",
        ]
        # Hacer dependencia opcional para que funcionarios no tengan que enviarla
        extra_kwargs = {"dependencia": {"required": False, "allow_null": True}}

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["imagen"] = (
            self.context["request"].build_absolute_uri(instance.imagen.url)
            if instance.imagen
            else None
        )

        # Mantener el valor crudo para edición, agregar display por separado
        representation["tipo_display"] = instance.get_tipo_display()

        representation["dependencia"] = (
            {
                "id": instance.dependencia.id,
                "nombre": instance.dependencia.nombre,
            }
            if instance.dependencia
            else None
        )

        return representation

    def get_cantidad_requisitos(self, obj):
        return obj.requisitos.count()

        return representation


class TramiteCatalogoListSerializer(serializers.ModelSerializer):
    """
    Serializer ligero para listados
    """

    nombre_dependencia = serializers.CharField(
        source="dependencia.nombre", read_only=True
    )
    cantidad_requisitos = serializers.SerializerMethodField()

    class Meta:
        model = TramiteCatalogo
        fields = [
            "id",
            "nombre",
            "tipo",
            "descripcion",
            "nombre_dependencia",
            "cantidad_requisitos",
            "destacado",
        ]

    def get_cantidad_requisitos(self, obj):
        return obj.requisitos.count()
