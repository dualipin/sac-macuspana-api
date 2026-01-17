from rest_framework import serializers
from django.db import transaction
from core.choices import Roles
from dependencias.models import Funcionario, Dependencia
from usuarios.models import Usuario

class DependenciaSerializer(serializers.ModelSerializer):
    titular_nombre = serializers.CharField(source='representante.nombre_completo', read_only=True)

    class Meta:
        model = Dependencia
        fields = '__all__'

class FuncionarioSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    nombre_dependencia = serializers.CharField(source='dependencia.nombre', read_only=True)

    class Meta:
        model = Funcionario
        fields = [
            'id', 'nombre_completo', 'correo', 'telefono', 'cargo', 
            'sexo', 'dependencia', 'nombre_dependencia', 'usuario',
            'username', 'password'
        ]
        read_only_fields = ['usuario']

    def create(self, validated_data):
        username = validated_data.pop('username')
        password = validated_data.pop('password')
        
        with transaction.atomic():
            user = Usuario.objects.create_user(
                username=username, 
                password=password, 
                rol=Roles.FUNCIONARIO
            )
            funcionario = Funcionario.objects.create(usuario=user, **validated_data)
            return funcionario
