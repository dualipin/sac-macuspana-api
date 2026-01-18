from rest_framework import serializers
from notificaciones.models import Notificacion


class NotificacionSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    folio_solicitud = serializers.SerializerMethodField()

    class Meta:
        model = Notificacion
        fields = [
            "id",
            "tipo",
            "tipo_display",
            "titulo",
            "mensaje",
            "leida",
            "fecha_creacion",
            "fecha_lectura",
            "folio_solicitud",
            "metadata",
            "email_enviado",
        ]
        read_only_fields = [
            "id",
            "fecha_creacion",
            "email_enviado",
        ]

    def get_folio_solicitud(self, obj):
        """Genera el folio de la solicitud si existe."""
        if obj.referencia_solicitud:
            return f"SOL-{obj.referencia_solicitud.id:06d}"
        return obj.metadata.get("folio", None)


class NotificacionListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados."""

    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = Notificacion
        fields = [
            "id",
            "tipo",
            "tipo_display",
            "titulo",
            "leida",
            "fecha_creacion",
        ]
