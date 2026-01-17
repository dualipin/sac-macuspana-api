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
        Filtrar solo programas activos para ciudadanos
        """
        queryset = super().get_queryset()

        # Si es ciudadano, solo mostrar programas activos
        if hasattr(self.request.user, "rol") and self.request.user.rol == "CIUDADANO":
            queryset = queryset.filter(esta_activo=True)

        return queryset
