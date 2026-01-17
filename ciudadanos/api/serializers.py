from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from rest_framework import serializers
from django.core import exceptions
from ciudadanos.models import Ciudadano
from ciudadanos.validators.curp import validate_curp_format, check_curp_unica
from core.choices import Roles
from localidades.api.serializers import LocalidadSerializer
from usuarios.api.serializers import UsuarioSerializer, UsuarioCreateSerializer
from usuarios.models import Usuario
from django.db import transaction


class RegistroCiudadanoSerializer(serializers.ModelSerializer):
    usuario = UsuarioCreateSerializer()

    class Meta:
        model = Ciudadano
        fields = [
            "curp",
            "nombre",
            "apellido_paterno",
            "apellido_materno",
            "fecha_nacimiento",
            "sexo",
            "correo",
            "telefono",
            "calle",
            "numero_exterior",
            "numero_interior",
            "localidad",
            "usuario",
        ]

    def validate(self, attrs):
        try:
            attrs["curp"] = validate_curp_format(attrs["curp"])
        except exceptions.ValidationError as e:
            raise serializers.ValidationError(e.messages)

        return attrs

    def validate_correo(self, value):
        import hashlib

        correo_hash = hashlib.sha256(value.lower().encode()).hexdigest()
        if Ciudadano.objects.filter(correo_hash=correo_hash).exists():
            raise serializers.ValidationError(
                "Este correo electrónico ya se encuentra registrado."
            )
        return value

    def create(self, validated_data: dict):
        usuario_data = validated_data.pop("usuario")
        curp = validated_data.pop("curp")
        correo_destino = validated_data.get("correo")

        with transaction.atomic():
            usuario = Usuario.objects.create_user(
                rol=Roles.CIUDADANO, username=curp, **usuario_data
            )

            ciudadano = Ciudadano.objects.create(
                usuario=usuario, curp=curp, **validated_data
            )

        self.enviar_correo_institucional(correo_destino, ciudadano.nombre, curp)

        return ciudadano

    def enviar_correo_institucional(self, email_destino, nombre, curp):
        context = {"nombre": nombre, "curp": curp, "web": settings.WEB_URL}

        # Renderiza el HTML con los datos del ciudadano
        html_content = render_to_string("bienvenida_email.html", context)
        # Crea una versión en texto plano para clientes que no soportan HTML
        text_content = strip_tags(html_content)

        print(f"Enviando correo a {email_destino}")

        try:
            send_mail(
                subject="Bienvenido al Registro Ciudadano - Macuspana",
                message=text_content,
                from_email=None,
                recipient_list=[email_destino],
                html_message=html_content,  # Este parámetro activa el formato visual
                fail_silently=False,
            )
        except Exception as e:
            print(f"Error al enviar correo: {e}")


class CiudadanoSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer()
    localidad = LocalidadSerializer(read_only=True)
    email = serializers.CharField(source="correo", read_only=True)
    correo = serializers.CharField(read_only=True)
    direccion = serializers.SerializerMethodField()

    class Meta:
        model = Ciudadano
        fields = [
            "id",
            "curp",
            "nombre",
            "apellido_paterno",
            "apellido_materno",
            "fecha_nacimiento",
            "sexo",
            "correo",
            "email",
            "telefono",
            "calle",
            "numero_exterior",
            "numero_interior",
            "localidad",
            "direccion",
            "usuario",
        ]

    def get_direccion(self, obj):
        """Construye la dirección completa"""
        if not obj.numero_interior:
            return f"{obj.calle}, {obj.numero_exterior}, {obj.localidad}"
        return f"{obj.calle}, {obj.numero_exterior}, {obj.numero_interior}, {obj.localidad}"


class CiudadanoUpdateSerializer(serializers.ModelSerializer):
    email = serializers.CharField(source="correo")

    class Meta:
        model = Ciudadano
        fields = ["nombre", "apellido_paterno", "apellido_materno", "email", "telefono"]

    def validate_email(self, value):
        """Validar que el email no exista para otro ciudadano"""
        import hashlib

        email_hash = hashlib.sha256(value.lower().encode()).hexdigest()

        # Buscar si el email ya existe
        existing = Ciudadano.objects.filter(correo_hash=email_hash).first()

        # Si existe y no es el mismo ciudadano, es un error
        if existing and existing.id != self.instance.id:
            raise serializers.ValidationError(
                "Este email ya está registrado para otro ciudadano"
            )

        return value

    def update(self, instance, validated_data):
        # Mapear email a correo
        if "correo" in validated_data:
            instance.correo = validated_data.pop("correo")

        # Actualizar otros campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class CiudadanoDireccionUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar la dirección del ciudadano"""

    localidad_id = serializers.IntegerField(write_only=True)
    codigo_postal = serializers.CharField(write_only=True, max_length=5)

    class Meta:
        model = Ciudadano
        fields = [
            "calle",
            "numero_exterior",
            "numero_interior",
            "localidad_id",
            "codigo_postal",
        ]
        extra_kwargs = {"numero_interior": {"required": False, "allow_blank": True}}

    def validate(self, attrs):
        """Validar que la localidad corresponda al código postal y sea de Macuspana, Tabasco"""
        from localidades.models import Localidad

        localidad_id = attrs.get("localidad_id")
        codigo_postal = attrs.get("codigo_postal")

        # Verificar que la localidad existe
        try:
            localidad = Localidad.objects.get(id=localidad_id)
        except Localidad.DoesNotExist:
            raise serializers.ValidationError(
                {"localidad_id": "La localidad seleccionada no existe."}
            )

        # Verificar que el código postal coincide con la localidad
        if localidad.codigo_postal != codigo_postal:
            raise serializers.ValidationError(
                {
                    "codigo_postal": "El código postal no coincide con la localidad seleccionada."
                }
            )

        # Verificar que la localidad pertenece a Macuspana, Tabasco
        if (
            localidad.municipio.upper() != "MACUSPANA"
            or localidad.estado.upper() != "TABASCO"
        ):
            raise serializers.ValidationError(
                {"localidad_id": "Solo se permiten direcciones en Macuspana, Tabasco."}
            )

        attrs["localidad"] = localidad
        return attrs

    def update(self, instance, validated_data):
        # Eliminar campos write_only antes de actualizar
        validated_data.pop("localidad_id", None)
        validated_data.pop("codigo_postal", None)

        # Actualizar campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
