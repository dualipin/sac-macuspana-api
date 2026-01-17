from rest_framework import serializers
from tramites.models import Solicitud, DocumentoSolicitud, SolicitudAsignacion
from core.choices import EstatusSolicitud, Roles
from ciudadanos.api.serializers import CiudadanoSerializer


class RequisitoSimpleSerializer(serializers.Serializer):
    """Serializer simple para requisito (anidado)"""

    id = serializers.IntegerField()
    nombre = serializers.CharField()
    es_obligatorio = serializers.BooleanField()
    requiere_documento = serializers.BooleanField()


class DependenciaSimpleSerializer(serializers.Serializer):
    """Serializer simple para dependencia (anidado)"""

    id = serializers.IntegerField()
    nombre = serializers.CharField()


class ProgramaSocialSimpleSerializer(serializers.Serializer):
    """Serializer simple para programa social (anidado)"""

    id = serializers.IntegerField()
    nombre = serializers.CharField()
    descripcion = serializers.CharField()
    dependencia = DependenciaSimpleSerializer(read_only=True)
    requisitos_especificos = RequisitoSimpleSerializer(many=True, read_only=True)


class DocumentoSolicitudSerializer(serializers.ModelSerializer):
    """
    Serializer para documentos de solicitudes
    """

    requisito = RequisitoSimpleSerializer(read_only=True)
    nombre_requisito = serializers.CharField(source="requisito.nombre", read_only=True)
    url_archivo = serializers.SerializerMethodField()

    class Meta:
        model = DocumentoSolicitud
        fields = [
            "id",
            "solicitud",
            "requisito",
            "nombre_requisito",
            "archivo",
            "url_archivo",
            "fecha_subida",
        ]
        read_only_fields = ["id", "fecha_subida"]

    def get_url_archivo(self, obj):
        request = self.context.get("request")
        if obj.archivo and request:
            return request.build_absolute_uri(obj.archivo.url)
        return None


class DocumentoSolicitudCreateSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para crear documentos
    """

    class Meta:
        model = DocumentoSolicitud
        fields = ["solicitud", "requisito", "archivo"]

    def validate(self, data):
        """
        Validar que el requisito corresponda al trámite o programa de la solicitud
        """
        solicitud = data.get("solicitud")
        requisito = data.get("requisito")

        # Verificar que el requisito pertenezca al trámite o programa de la solicitud
        if solicitud.programa_social:
            if requisito.programa != solicitud.programa_social:
                raise serializers.ValidationError(
                    "El requisito no pertenece al programa social de esta solicitud"
                )
        else:
            if requisito.tramite != solicitud.tramite_tipo:
                raise serializers.ValidationError(
                    "El requisito no pertenece al trámite de esta solicitud"
                )

        return data


class SolicitudAsignacionSerializer(serializers.ModelSerializer):
    """
    Serializer para asignaciones de solicitudes
    """

    nombre_funcionario = serializers.SerializerMethodField()
    nombre_dependencia = serializers.CharField(
        source="dependencia.nombre", read_only=True
    )
    asignado_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model = SolicitudAsignacion
        fields = [
            "id",
            "solicitud",
            "funcionario",
            "nombre_funcionario",
            "dependencia",
            "nombre_dependencia",
            "fecha_asignacion",
            "asignado_por",
            "asignado_por_nombre",
            "es_asignacion_automatica",
            "activo",
            "notas",
        ]
        read_only_fields = ["id", "fecha_asignacion"]

    def get_nombre_funcionario(self, obj):
        # Asumiendo que Usuario tiene relación con Funcionario o Ciudadano
        return obj.funcionario.username

    def get_asignado_por_nombre(self, obj):
        return obj.asignado_por.username if obj.asignado_por else "Sistema (automático)"


class SolicitudSerializer(serializers.ModelSerializer):
    """
    Serializer completo para solicitudes con documentos y asignaciones
    """

    ciudadano = CiudadanoSerializer(read_only=True)
    programa_social = ProgramaSocialSimpleSerializer(read_only=True)
    documentos = DocumentoSolicitudSerializer(many=True, read_only=True)
    asignaciones = SolicitudAsignacionSerializer(many=True, read_only=True)
    nombre_ciudadano = serializers.SerializerMethodField()
    nombre_tramite = serializers.CharField(source="tramite_tipo.nombre", read_only=True)
    nombre_programa = serializers.CharField(
        source="programa_social.nombre", read_only=True, allow_null=True
    )
    documentacion_completa = serializers.SerializerMethodField()
    estatus_display = serializers.CharField(
        source="get_estatus_display", read_only=True
    )
    nombre_dependencia = serializers.SerializerMethodField()
    # Alias para mantener compatibilidad con frontend
    fecha_creacion = serializers.DateTimeField(source="created_at", read_only=True)
    fecha_actualizacion = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = Solicitud
        fields = [
            "id",
            "ciudadano",
            "nombre_ciudadano",
            "tramite_tipo",
            "nombre_tramite",
            "programa_social",
            "nombre_programa",
            "nombre_dependencia",
            "estatus",
            "estatus_display",
            "descripcion_ciudadano",
            "comentarios_revision",
            "documentos",
            "asignaciones",
            "documentacion_completa",
            "created_at",
            "updated_at",
            "fecha_creacion",
            "fecha_actualizacion",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_nombre_ciudadano(self, obj):
        return f"{obj.ciudadano.nombre} {obj.ciudadano.apellido_paterno}"

    def get_documentacion_completa(self, obj):
        return obj.verificar_documentacion_completa()

    def get_nombre_dependencia(self, obj):
        """Nombre de la dependencia a la que está dirigida la solicitud"""
        # Priorizar programa social si existe, luego trámite
        if obj.programa_social:
            return obj.programa_social.dependencia.nombre
        if obj.tramite_tipo:
            return obj.tramite_tipo.dependencia.nombre
        return "N/A"


class SolicitudCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear solicitudes con documentos
    """

    class Meta:
        model = Solicitud
        fields = [
            "ciudadano",
            "tramite_tipo",
            "programa_social",
            "descripcion_ciudadano",
        ]

    def validate(self, data):
        """
        Validaciones al crear solicitud
        """
        tramite_tipo = data.get("tramite_tipo")
        programa_social = data.get("programa_social")

        # Validar que se especifique trámite O programa (al menos uno)
        if not tramite_tipo and not programa_social:
            raise serializers.ValidationError(
                "Debe especificar un trámite o programa social"
            )

        return data

    def create(self, validated_data):
        # Crear la solicitud (el estatus se establece automáticamente como PENDIENTE)
        solicitud = super().create(validated_data)

        # Procesar documentos del request
        request = self.context.get("request")
        if request:
            self._crear_documentos(solicitud, request)

        return solicitud

    def _crear_documentos(self, solicitud, request):
        """
        Procesa los archivos documentos_* y crea registros de DocumentoSolicitud
        """
        # Obtener requisitos que requieren documento
        if solicitud.programa_social:
            requisitos = solicitud.programa_social.requisitos_especificos.filter(
                requiere_documento=True
            )
        else:
            requisitos = solicitud.tramite_tipo.requisitos.filter(
                requiere_documento=True
            )

        # Procesar cada archivo documentos_*
        for requisito in requisitos:
            file_key = f"documentos_{requisito.id}"
            archivo = request.FILES.get(file_key)

            if archivo:
                try:
                    DocumentoSolicitud.objects.create(
                        solicitud=solicitud, requisito=requisito, archivo=archivo
                    )
                except Exception as e:
                    # Log pero no fallar la creación de solicitud
                    # El documento simplemente no se crea
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.error(
                        f"Error al crear documento para requisito {requisito.id}: {str(e)}"
                    )


class SolicitudListSerializer(serializers.ModelSerializer):
    """
    Serializer ligero para listados
    """

    ciudadano = CiudadanoSerializer(read_only=True)
    programa_social = ProgramaSocialSimpleSerializer(read_only=True)
    nombre_ciudadano = serializers.SerializerMethodField()
    nombre_tramite = serializers.CharField(source="tramite_tipo.nombre", read_only=True)
    nombre_programa = serializers.CharField(
        source="programa_social.nombre", read_only=True, allow_null=True
    )
    estatus_display = serializers.CharField(
        source="get_estatus_display", read_only=True
    )
    documentacion_completa = serializers.SerializerMethodField()
    nombre_dependencia = serializers.SerializerMethodField()
    folio = serializers.CharField(source="id", read_only=True)
    # Alias para mantener compatibilidad con frontend
    fecha_creacion = serializers.DateTimeField(source="created_at", read_only=True)
    fecha_actualizacion = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = Solicitud
        fields = [
            "id",
            "folio",
            "ciudadano",
            "nombre_ciudadano",
            "nombre_tramite",
            "nombre_programa",
            "programa_social",
            "estatus",
            "estatus_display",
            "descripcion_ciudadano",
            "documentacion_completa",
            "created_at",
            "updated_at",
            "fecha_creacion",
            "fecha_actualizacion",
            "nombre_dependencia",
        ]

    def get_nombre_ciudadano(self, obj):
        return f"{obj.ciudadano.nombre} {obj.ciudadano.apellido_paterno}"

    def get_documentacion_completa(self, obj):
        return obj.verificar_documentacion_completa()

    def get_nombre_dependencia(self, obj):
        # Priorizar programa social si existe, luego trámite
        if obj.programa_social:
            return obj.programa_social.dependencia.nombre
        if obj.tramite_tipo:
            return obj.tramite_tipo.dependencia.nombre
        return "N/A"


class SolicitudHistorialSerializer(serializers.Serializer):
    """
    Serializer para el historial de cambios de una solicitud
    """

    id = serializers.IntegerField()
    estatus = serializers.CharField()
    estatus_display = serializers.CharField()
    fecha = serializers.DateTimeField(source="history_date")
    cambio_por = serializers.SerializerMethodField()
    cambio_tipo = serializers.CharField(source="get_history_type_display")

    def get_cambio_por(self, obj):
        """Obtener nombre del usuario que hizo el cambio"""
        if obj.history_user:
            usuario = obj.history_user
            if hasattr(usuario, "ciudadano"):
                return (
                    f"{usuario.ciudadano.nombre} {usuario.ciudadano.apellido_paterno}"
                )
            return usuario.username
        return "Sistema"


class CambiarEstatusSolicitudSerializer(serializers.Serializer):
    """
    Serializer para cambiar el estatus de una solicitud
    """

    estatus = serializers.ChoiceField(choices=EstatusSolicitud.choices)
    comentarios_revision = serializers.CharField(required=False, allow_blank=True)

    def validate_estatus(self, value):
        """
        Validar transiciones de estado permitidas
        """
        solicitud = self.context.get("solicitud")
        usuario = self.context.get("request").user

        # Solo funcionarios y administradores pueden cambiar estados
        if usuario.rol not in [Roles.ADMINISTRADOR, Roles.FUNCIONARIO]:
            raise serializers.ValidationError(
                "No tiene permisos para cambiar el estatus"
            )

        # Validar transiciones lógicas (opcional)
        # Por ejemplo, no permitir pasar de RECHAZADO a APROBADO directamente

        return value
