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
