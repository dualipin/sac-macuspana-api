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

    def get_queryset(self):
        """
        Filtrar trámites según el rol del usuario:
        - Funcionarios: solo trámites de su dependencia
        - Administradores y otros: todos los trámites
        """
        queryset = super().get_queryset()
        user = self.request.user

        # Si es funcionario, solo mostrar trámites de su dependencia
        if hasattr(user, "rol") and user.rol == "FUNCIONARIO":
            # Asegurar que se carga la relación funcionario
            if (
                not hasattr(user, "_prefetched_objects_cache")
                or "funcionario" not in user.__dict__
            ):
                user = self.request.user.__class__.objects.select_related(
                    "funcionario"
                ).get(pk=user.pk)

            if hasattr(user, "funcionario") and user.funcionario:
                queryset = queryset.filter(dependencia=user.funcionario.dependencia)
            else:
                # Si no tiene perfil de funcionario asociado, no mostrar nada
                queryset = queryset.none()

        return queryset

    def perform_create(self, serializer):
        """
        Validar que el funcionario solo cree trámites para su dependencia
        """
        user = self.request.user

        # Si es funcionario, forzar su dependencia
        if user.rol == "FUNCIONARIO":
            if not hasattr(user, "funcionario"):
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied(
                    "El usuario no tiene un perfil de funcionario asociado."
                )

            serializer.save(dependencia=user.funcionario.dependencia)
        else:
            # Administradores pueden guardar tal cual viene (con la dependencia elegida)
            serializer.save()

    def perform_update(self, serializer):
        """
        Validar que el funcionario solo edite trámites de su dependencia
        """
        user = self.request.user
        instance = self.get_object()

        # Si es funcionario, verificar que el trámite pertenezca a su dependencia
        if user.rol == "FUNCIONARIO":
            if not hasattr(user, "funcionario"):
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied(
                    "El usuario no tiene un perfil de funcionario asociado."
                )

            if instance.dependencia != user.funcionario.dependencia:
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied(
                    "No tienes permiso para editar trámites de otra dependencia."
                )

            # Al guardar, asegurarnos de que no cambie la dependencia
            serializer.save(dependencia=user.funcionario.dependencia)
        else:
            serializer.save()

    def perform_destroy(self, instance):
        """
        Validar que el funcionario solo elimine trámites de su dependencia
        """
        user = self.request.user

        # Si es funcionario, verificar que el trámite pertenezca a su dependencia
        if user.rol == "FUNCIONARIO":
            if not hasattr(user, "funcionario"):
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied(
                    "El usuario no tiene un perfil de funcionario asociado."
                )

            if instance.dependencia != user.funcionario.dependencia:
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied(
                    "No tienes permiso para eliminar trámites de otra dependencia."
                )

        instance.delete()


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

        if not hasattr(user, "funcionario"):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "El usuario no tiene un perfil de funcionario asociado."
            )

        dependencia_usuario = user.funcionario.dependencia

        if tramite and tramite.dependencia != dependencia_usuario:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("No tienes permiso sobre este trámite.")

        if programa and programa.dependencia != dependencia_usuario:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("No tienes permiso sobre este programa social.")

    def perform_create(self, serializer):
        tramite = serializer.validated_data.get("tramite")
        programa = serializer.validated_data.get("programa")

        self._validar_propiedad_dependencia(tramite, programa)
        serializer.save()

    def perform_update(self, serializer):
        instance = self.get_object()
        # Verificar el objeto actual
        self._validar_propiedad_dependencia(instance.tramite, instance.programa)

        # Verificar si intenta cambiarlo a otro padre que no le pertenece
        nuevo_tramite = serializer.validated_data.get("tramite", instance.tramite)
        nuevo_programa = serializer.validated_data.get("programa", instance.programa)

        self._validar_propiedad_dependencia(nuevo_tramite, nuevo_programa)
        serializer.save()

    def perform_destroy(self, instance):
        self._validar_propiedad_dependencia(instance.tramite, instance.programa)
        instance.delete()
