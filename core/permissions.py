from rest_framework import permissions
from core.choices import Roles


class IsAdministrador(permissions.BasePermission):
    """
    Permiso que solo permite acceso a usuarios con rol ADMINISTRADOR
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol == Roles.ADMINISTRADOR
        )


class IsFuncionario(permissions.BasePermission):
    """
    Permiso que solo permite acceso a usuarios con rol FUNCIONARIO
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol == Roles.FUNCIONARIO
        )


class IsCiudadano(permissions.BasePermission):
    """
    Permiso que solo permite acceso a usuarios con rol CIUDADANO
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol == Roles.CIUDADANO
        )


class IsAdministradorOrFuncionario(permissions.BasePermission):
    """
    Permiso que permite acceso a ADMINISTRADOR o FUNCIONARIO
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol in [Roles.ADMINISTRADOR, Roles.FUNCIONARIO]
        )


class IsOwnerOrStaff(permissions.BasePermission):
    """
    Permiso que permite al ciudadano ver solo sus propias solicitudes,
    pero permite a funcionarios y administradores ver todas
    """

    def has_object_permission(self, request, view, obj):
        # Staff (funcionarios y administradores) pueden ver todo
        if request.user.rol in [Roles.ADMINISTRADOR, Roles.FUNCIONARIO]:
            return True

        # Ciudadanos solo pueden ver sus propias solicitudes
        if hasattr(obj, "ciudadano"):
            return obj.ciudadano.usuario == request.user

        return False


class ReadOnlyOrStaff(permissions.BasePermission):
    """
    Permiso de solo lectura para todos, escritura solo para staff
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol in [Roles.ADMINISTRADOR, Roles.FUNCIONARIO]
        )


class ReadOnlyPublicOrStaff(permissions.BasePermission):
    """
    Permiso de solo lectura pública (sin autenticación), escritura solo para staff
    """

    def has_permission(self, request, view):
        # Lectura permitida para todos (autenticados y sin autenticar)
        if request.method in permissions.SAFE_METHODS:
            return True

        # Escritura solo para staff autenticado
        # Escritura solo para staff autenticado
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol in [Roles.ADMINISTRADOR, Roles.FUNCIONARIO]
        )


class IsFuncionarioDeDependencia(permissions.BasePermission):
    """
    Permite acceso a funcionarios solo si el objeto pertenece a su dependencia
    o si tienen una asignación explícita activa.
    """

    def has_permission(self, request, view):
        # Permiso a nivel vista: solo valida que sea funcionario
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol == Roles.FUNCIONARIO
            and hasattr(request.user, "funcionario")
        )

    def has_object_permission(self, request, view, obj):
        # Validar lógica de negocio sobre el objeto
        funcionario = request.user.funcionario

        # Caso 1: Solicitud (verificar si el trámite/programa es de mi dependencia)
        # Verificar dependencia del trámite
        if hasattr(obj, "tramite_tipo") and obj.tramite_tipo.dependencia == funcionario.dependencia:
            return True

        # Verificar dependencia del programa social
        if (
            hasattr(obj, "programa_social")
            and obj.programa_social
            and obj.programa_social.dependencia == funcionario.dependencia
        ):
            return True

        # Caso 2: Asignación explícita
        # Verificar si hay asignación activa para este funcionario
        if hasattr(obj, "asignaciones"):
            if obj.asignaciones.filter(funcionario=request.user, activo=True).exists():
                return True

        return False
