from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated

from apoyos.models import ProgramaSocial
from core.permissions import IsAdministradorOrFuncionario, ReadOnlyOrStaff, ReadOnlyPublicOrStaff
from .serializers import (
    ProgramaSocialSerializer,
    ProgramaSocialCreateUpdateSerializer,
    ProgramaSocialListSerializer,
)


from ..filters import ProgramaSocialFilter


class ProgramaSocialViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar programas sociales.
    - Lectura: Todos los usuarios autenticados
    - Escritura: Solo administradores y funcionarios
    """

    queryset = ProgramaSocial.objects.all()
    serializer_class = ProgramaSocialSerializer
    permission_classes = [ReadOnlyPublicOrStaff]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = ProgramaSocialFilter
    search_fields = ["nombre", "descripcion"]
    ordering_fields = ["nombre"]
    ordering = ["nombre"]

    def get_serializer_class(self):
        if self.action == "list":
            return ProgramaSocialListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return ProgramaSocialCreateUpdateSerializer
        return ProgramaSocialSerializer

    def get_queryset(self):
        """
        Filtrar programas según el rol del usuario:
        - Ciudadanos: solo programas activos
        - Funcionarios: solo programas de su dependencia
        - Administradores: todos los programas
        """
        queryset = super().get_queryset()
        user = self.request.user

        # Si es ciudadano, solo mostrar programas activos
        if hasattr(user, "rol") and user.rol == "CIUDADANO":
            queryset = queryset.filter(esta_activo=True)
        
        # Si es funcionario, solo mostrar programas de su dependencia
        elif hasattr(user, "rol") and user.rol == "FUNCIONARIO":
            if hasattr(user, 'funcionario') and user.funcionario:
                queryset = queryset.filter(dependencia=user.funcionario.dependencia)
            else:
                # Si no tiene perfil de funcionario asociado, no mostrar nada
                queryset = queryset.none()

        return queryset

    def perform_create(self, serializer):
        """
        Validar que el funcionario solo cree programas para su dependencia
        """
        user = self.request.user
        
        # Si es funcionario, forzar su dependencia
        if user.rol == "FUNCIONARIO":
            if not hasattr(user, 'funcionario'):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("El usuario no tiene un perfil de funcionario asociado.")
            
            serializer.save(dependencia=user.funcionario.dependencia)
        else:
            # Administradores pueden guardar tal cual viene (con la dependencia elegida)
            serializer.save()

    def perform_update(self, serializer):
        """
        Validar que el funcionario solo edite programas de su dependencia
        """
        user = self.request.user
        instance = self.get_object()

        # Si es funcionario, verificar que el programa pertenezca a su dependencia
        if user.rol == "FUNCIONARIO":
            if not hasattr(user, 'funcionario'):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("El usuario no tiene un perfil de funcionario asociado.")
            
            if instance.dependencia != user.funcionario.dependencia:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("No tienes permiso para editar programas de otra dependencia.")
            
            # Al guardar, asegurarnos de que no cambie la dependencia
            serializer.save(dependencia=user.funcionario.dependencia)
        else:
            serializer.save()

    def perform_destroy(self, instance):
        """
        Validar que el funcionario solo elimine programas de su dependencia
        """
        user = self.request.user

        # Si es funcionario, verificar que el programa pertenezca a su dependencia
        if user.rol == "FUNCIONARIO":
            if not hasattr(user, 'funcionario'):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("El usuario no tiene un perfil de funcionario asociado.")
            
            if instance.dependencia != user.funcionario.dependencia:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("No tienes permiso para eliminar programas de otra dependencia.")
        
        instance.delete()
