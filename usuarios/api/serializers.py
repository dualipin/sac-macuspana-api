from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from core.choices import Roles
from dependencias.api.serializers import FuncionarioSerializer
from usuarios.models import Usuario


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user: Usuario):
        token = super().get_token(user)

        # Agregar información personalizada al token
        token['username'] = user.username
        token['rol'] = user.rol

        return token


class PerfilSerializer(serializers.ModelSerializer):
    detalle_perfil = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ['id', 'rol', 'username', 'detalle_perfil']

    def get_detalle_perfil(self, obj: Usuario):
        from ciudadanos.api.serializers import CiudadanoSerializer

        if obj.rol == Roles.CIUDADANO.value and hasattr(obj, 'ciudadano'):
            return CiudadanoSerializer(obj.ciudadano).data
        if (obj.rol == Roles.FUNCIONARIO or obj.rol == Roles.ADMINISTRADOR) and hasattr(obj, 'funcionario'):
            return FuncionarioSerializer(obj.funcionario).data
        return None


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['username', 'password', 'rol']
        extra_kwargs = {'password': {'write_only': True}}


class UsuarioCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['password']
        extra_kwargs = {'password': {'write_only': True}}


class CambiarContrasenaSerializer(serializers.Serializer):
    contrasena_actual = serializers.CharField(write_only=True, required=True)
    contrasena_nueva = serializers.CharField(write_only=True, required=True, min_length=8)
    confirmar_contrasena = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        if attrs['contrasena_nueva'] != attrs['confirmar_contrasena']:
            raise serializers.ValidationError({"confirmar_contrasena": "Las contraseñas no coinciden."})
        return attrs

    def validate_contrasena_actual(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("La contraseña actual es incorrecta.")
        return value


class ActualizarContactoCiudadanoSerializer(serializers.Serializer):
    correo = serializers.EmailField(required=True)
    telefono = serializers.CharField(required=True, max_length=15)

    def validate_correo(self, value):
        from ciudadanos.models import Ciudadano
        import hashlib
        
        # Obtener el ciudadano actual del contexto
        request = self.context.get('request')
        if not request or not hasattr(request.user, 'ciudadano'):
            return value
        
        # Generar hash del nuevo correo
        correo_hash = hashlib.sha256(value.encode()).hexdigest()
        
        # Verificar si el correo ya existe (excluyendo al ciudadano actual)
        if Ciudadano.objects.filter(correo_hash=correo_hash).exclude(id=request.user.ciudadano.id).exists():
            raise serializers.ValidationError("Este correo electrónico ya está registrado en el sistema.")
        
        return value


class UsuarioListSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.SerializerMethodField()
    detalle_perfil = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ['id', 'username', 'rol', 'nombre_completo', 'detalle_perfil', 'is_active']

    def get_nombre_completo(self, obj: Usuario):
        if obj.rol == Roles.CIUDADANO.value and hasattr(obj, 'ciudadano'):
            return f"{obj.ciudadano.nombre} {obj.ciudadano.apellido_paterno} {obj.ciudadano.apellido_materno or ''}".strip()
        if (obj.rol == Roles.FUNCIONARIO or obj.rol == Roles.ADMINISTRADOR) and hasattr(obj, 'funcionario'):
            return obj.funcionario.nombre_completo
        return "Sin perfil"
        
    def get_detalle_perfil(self, obj: Usuario):
        if obj.rol == Roles.CIUDADANO.value and hasattr(obj, 'ciudadano'):
            from ciudadanos.api.serializers import CiudadanoSerializer
            return CiudadanoSerializer(obj.ciudadano).data
        if (obj.rol == Roles.FUNCIONARIO or obj.rol == Roles.ADMINISTRADOR) and hasattr(obj, 'funcionario'):
            return FuncionarioSerializer(obj.funcionario).data
        return None


class AdminPasswordResetSerializer(serializers.Serializer):
    nueva_contrasena = serializers.CharField(write_only=True, required=True, min_length=8)


class ChangeUserRoleSerializer(serializers.Serializer):
    rol = serializers.ChoiceField(choices=Roles)
    # Fields required if promoting to FUNCIONARIO
    dependencia_id = serializers.IntegerField(required=False, write_only=True)
    cargo = serializers.CharField(required=False, write_only=True)
    telefono = serializers.CharField(required=False, write_only=True)
    sexo = serializers.CharField(required=False, write_only=True)

    def validate(self, attrs):
        rol = attrs.get('rol')
        if rol == Roles.FUNCIONARIO:
            if not attrs.get('dependencia_id'):
                raise serializers.ValidationError({"dependencia_id": "Este campo es requerido para funcionarios."})
            if not attrs.get('cargo'):
                raise serializers.ValidationError({"cargo": "Este campo es requerido para funcionarios."})
        return attrs


class ChangeUserRoleSerializer(serializers.Serializer):
    rol = serializers.ChoiceField(choices=Roles)
    # Fields required if promoting to FUNCIONARIO
    dependencia_id = serializers.IntegerField(required=False, write_only=True)
    cargo = serializers.CharField(required=False, write_only=True)
    telefono = serializers.CharField(required=False, write_only=True)
    sexo = serializers.CharField(required=False, write_only=True)

    def validate(self, attrs):
        rol = attrs.get('rol')
        if rol == Roles.FUNCIONARIO:
            if not attrs.get('dependencia_id'):
                raise serializers.ValidationError({"dependencia_id": "Este campo es requerido para funcionarios."})
            if not attrs.get('cargo'):
                raise serializers.ValidationError({"cargo": "Este campo es requerido para funcionarios."})
        return attrs

