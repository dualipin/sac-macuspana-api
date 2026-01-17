from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated

from servicios.models import TramiteCatalogo, Requisito
from core.permissions import (
    IsAdministradorOrFuncionario,
    ReadOnlyOrStaff,
    ReadOnlyPublicOrStaff,
)
from .serializers import (
    TramiteCatalogoSerializer,
    TramiteCatalogoListSerializer,
    RequisitoSerializer,
    RequisitoCreateSerializer,
)
from ..filters import TramiteCatalogoFilter


class TramiteCatalogoViewSet(viewsets.ModelViewSet):
    queryset = TramiteCatalogo.objects.all()
    serializer_class = TramiteCatalogoSerializer
    permission_classes = [ReadOnlyPublicOrStaff]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = TramiteCatalogoFilter
    search_fields = ["nombre", "descripcion"]
    ordering_fields = ["nombre", "id"]
    ordering = ["nombre"]

    def get_serializer_class(self):
        if self.action == "list":
            return TramiteCatalogoListSerializer
        return TramiteCatalogoSerializer


class RequisitoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar requisitos de trámites y programas sociales.
    Solo administradores y funcionarios pueden crear/editar.
    """

    queryset = Requisito.objects.all()
    serializer_class = RequisitoSerializer
    permission_classes = [IsAuthenticated, IsAdministradorOrFuncionario]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["tramite", "programa", "es_obligatorio", "requiere_documento"]
    search_fields = ["nombre"]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return RequisitoCreateSerializer
        return RequisitoSerializer

    def _validar_propiedad_dependencia(self, tramite=None, programa=None):
        """
        Valida que el funcionario tenga permiso sobre el trámite o programa
        """
        user = self.request.user
        if user.rol != "FUNCIONARIO":
            return

        if not hasattr(user, 'funcionario'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("El usuario no tiene un perfil de funcionario asociado.")

        dependencia_usuario = user.funcionario.dependencia

        if tramite and tramite.dependencia != dependencia_usuario:
             from rest_framework.exceptions import PermissionDenied
             raise PermissionDenied("No tienes permiso sobre este trámite.")
        
        if programa and programa.dependencia != dependencia_usuario:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("No tienes permiso sobre este programa social.")

    def perform_create(self, serializer):
        tramite = serializer.validated_data.get('tramite')
        programa = serializer.validated_data.get('programa')
        
        self._validar_propiedad_dependencia(tramite, programa)
        serializer.save()

    def perform_update(self, serializer):
        instance = self.get_object()
        # Verificar el objeto actual
        self._validar_propiedad_dependencia(instance.tramite, instance.programa)
        
        # Verificar si intenta cambiarlo a otro padre que no le pertenece
        nuevo_tramite = serializer.validated_data.get('tramite', instance.tramite)
        nuevo_programa = serializer.validated_data.get('programa', instance.programa)
        
        self._validar_propiedad_dependencia(nuevo_tramite, nuevo_programa)
        serializer.save()

    def perform_destroy(self, instance):
        self._validar_propiedad_dependencia(instance.tramite, instance.programa)
        instance.delete()
