from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import (
    CustomTokenObtainPairSerializer,
    PerfilSerializer,
    CambiarContrasenaSerializer,
    ActualizarContactoCiudadanoSerializer,
    UsuarioListSerializer,
    AdminPasswordResetSerializer,
    ChangeUserRoleSerializer,
)
from rest_framework.views import APIView
from rest_framework import status
from core.choices import Roles


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class PerfileView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        serializer = PerfilSerializer(request.user)
        return Response(serializer.data)


class CambiarContrasenaView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CambiarContrasenaSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            request.user.set_password(serializer.validated_data['contrasena_nueva'])
            request.user.save()
            return Response(
                {"mensaje": "Contraseña actualizada exitosamente."},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ActualizarContactoCiudadanoView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        if request.user.rol != Roles.CIUDADANO.value:
            return Response(
                {"error": "Solo los ciudadanos pueden actualizar sus datos de contacto."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not hasattr(request.user, 'ciudadano'):
            return Response(
                {"error": "No se encontró el perfil de ciudadano."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ActualizarContactoCiudadanoSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            ciudadano = request.user.ciudadano
            ciudadano.correo = serializer.validated_data['correo']
            ciudadano.telefono = serializer.validated_data['telefono']
            ciudadano.save()
            return Response(
                {"mensaje": "Datos de contacto actualizados exitosamente."},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from rest_framework import generics, filters
from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination
from django_filters.rest_framework import DjangoFilterBackend
from usuarios.models import Usuario

class StandardResultsSetPagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 100

class UsuarioListView(generics.ListAPIView):
    queryset = Usuario.objects.all().order_by('-id').distinct()
    serializer_class = UsuarioListSerializer
    permission_classes = [IsAuthenticated] # TODO: Add IsAdminUser
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['username', 'ciudadano__nombre', 'ciudadano__apellido_paterno', 'funcionario__nombre_completo']
    filterset_fields = ['rol']
    
    def get_queryset(self):
        # Allow filtering by role through query params if needed beyond basic filterset
        queryset = super().get_queryset()
        return queryset


class CambiarContrasenaAdminView(APIView):
    permission_classes = [IsAuthenticated] # TODO: Add IsAdminUser

    def post(self, request, pk):
        try:
            user = Usuario.objects.get(pk=pk)
        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)
            
        serializer = AdminPasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            user.set_password(serializer.validated_data['nueva_contrasena'])
            user.save()
            return Response(
                {"mensaje": "Contraseña actualizada exitosamente por el administrador."},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangeUserRoleView(APIView):
    permission_classes = [IsAuthenticated] # TODO: Add IsAdminUser

    def post(self, request, pk):
        try:
            user = Usuario.objects.get(pk=pk)
        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ChangeUserRoleSerializer(data=request.data)
        if serializer.is_valid():
            new_role = serializer.validated_data['rol']
            
            # If promoting to FUNCIONARIO
            if new_role == Roles.FUNCIONARIO and user.rol != Roles.FUNCIONARIO:
                from dependencias.models import Funcionario, Dependencia
                
                dependencia_id = serializer.validated_data['dependencia_id']
                try:
                    dependencia = Dependencia.objects.get(pk=dependencia_id)
                except Dependencia.DoesNotExist:
                    return Response({"error": "Dependencia no encontrada."}, status=status.HTTP_400_BAD_REQUEST)

                # Check if user already has a Funcionario profile (maybe soft deleted)
                if hasattr(user, 'funcionario'):
                    funcionario = user.funcionario
                    funcionario.dependencia = dependencia
                    funcionario.cargo = serializer.validated_data['cargo']
                    funcionario.telefono = serializer.validated_data.get('telefono', '')
                    funcionario.sexo = serializer.validated_data.get('sexo', 'O')
                    funcionario.save()
                else:
                    # Create new Funcionario profile
                    # Try to get basic info from Citizen profile if exists, otherwise require simple inputs
                    nombre = user.username
                    correo = f"{user.username}@macuspana.gob.mx" # Placeholder logic
                    
                    if hasattr(user, 'ciudadano'):
                        nombre = f"{user.ciudadano.nombre} {user.ciudadano.apellido_paterno} {user.ciudadano.apellido_materno or ''}".strip()
                        correo = user.ciudadano.email or correo
                    
                    Funcionario.objects.create(
                        usuario=user,
                        nombre_completo=nombre,
                        correo=correo,
                        dependencia=dependencia,
                        cargo=serializer.validated_data['cargo'],
                        telefono=serializer.validated_data.get('telefono', ''),
                        sexo=serializer.validated_data.get('sexo', 'O')
                    )
            
            user.rol = new_role
            user.save()
            
            return Response(
                {"mensaje": f"Rol actualizado a {new_role} exitosamente."},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangeUserStatusView(APIView):
    permission_classes = [IsAuthenticated] # TODO: Add IsAdminUser

    def post(self, request, pk):
        try:
            user = Usuario.objects.get(pk=pk)
        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        # Toggle status
        user.is_active = not user.is_active
        user.save()

        status_msg = "activado" if user.is_active else "desactivado"
        return Response(
            {"mensaje": f"Usuario {status_msg} exitosamente.", "is_active": user.is_active},
            status=status.HTTP_200_OK
        )
