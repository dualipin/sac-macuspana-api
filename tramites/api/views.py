from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import os

from tramites.models import Solicitud, DocumentoSolicitud, SolicitudAsignacion
from core.permissions import (
    IsOwnerOrStaff,
    IsAdministradorOrFuncionario,
    IsCiudadano,
    IsFuncionarioDeDependencia,
)
from core.choices import Roles, EstatusSolicitud
from rest_framework.views import APIView
from django.db.models import Count, Q

from .serializers import (
    SolicitudSerializer,
    SolicitudCreateSerializer,
    SolicitudListSerializer,
    DocumentoSolicitudSerializer,
    DocumentoSolicitudCreateSerializer,
    SolicitudAsignacionSerializer,
    CambiarEstatusSolicitudSerializer,
)


class SolicitudViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar solicitudes de ciudadanos.
    - Ciudadanos: Solo pueden ver y crear sus propias solicitudes
    - Funcionarios/Admins: Pueden ver todas y cambiar estados
    """

    queryset = Solicitud.objects.select_related(
        "ciudadano", "tramite_tipo", "programa_social"
    ).prefetch_related("documentos", "asignaciones")
    serializer_class = SolicitudSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["estatus", "tramite_tipo", "programa_social", "ciudadano"]
    search_fields = [
        "descripcion_ciudadano",
        "ciudadano__nombre",
        "ciudadano__apellido_paterno",
    ]
    ordering_fields = ["id", "estatus"]
    ordering = ["-id"]

    def get_serializer_class(self):
        if self.action == "list":
            return SolicitudListSerializer
        elif self.action == "create":
            return SolicitudCreateSerializer
        elif self.action == "cambiar_estatus":
            return CambiarEstatusSolicitudSerializer
        return SolicitudSerializer

        return queryset

    def get_queryset(self):
        """
        Filtrar solicitudes según el rol del usuario
        """
        queryset = super().get_queryset()
        user = self.request.user

        if user.rol == Roles.CIUDADANO:
            # Ciudadanos solo ven sus propias solicitudes
            queryset = queryset.filter(ciudadano__usuario=user)
        elif user.rol == Roles.FUNCIONARIO:
            # Funcionarios ven:
            # 1. Solicitudes de su dependencia (por trámite o programa)
            # 2. Solicitudes asignadas explícitamente a ellos
            if hasattr(user, "funcionario"):
                dependencia = user.funcionario.dependencia
                queryset = queryset.filter(
                    Q(tramite_tipo__dependencia=dependencia)
                    | Q(programa_social__dependencia=dependencia)
                    | Q(asignaciones__funcionario=user, asignaciones__activo=True)
                ).distinct()

        return queryset

    def perform_create(self, serializer):
        """
        Al crear, asociar automáticamente al ciudadano del usuario actual
        """
        # Obtener el ciudadano asociado al usuario
        ciudadano = self.request.user.ciudadano
        serializer.save(ciudadano=ciudadano)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsAdministradorOrFuncionario],
    )
    def cambiar_estatus(self, request, pk=None):
        """
        Endpoint para que funcionarios cambien el estatus de una solicitud
        POST /api/tramites/solicitudes/{id}/cambiar_estatus/
        Body: {"estatus": "APROBADO", "comentarios_revision": "..."}
        """
        solicitud = self.get_object()
        serializer = CambiarEstatusSolicitudSerializer(
            data=request.data, context={"solicitud": solicitud, "request": request}
        )
        serializer.is_valid(raise_exception=True)

        solicitud.estatus = serializer.validated_data["estatus"]
        if "comentarios_revision" in serializer.validated_data:
            solicitud.comentarios_revision = serializer.validated_data[
                "comentarios_revision"
            ]
        solicitud.save()

        # Aquí se podría disparar una notificación al ciudadano

        return Response(
            SolicitudSerializer(solicitud, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"])
    def verificar_documentacion(self, request, pk=None):
        """
        Verificar si la documentación está completa
        GET /api/tramites/solicitudes/{id}/verificar_documentacion/
        """
        solicitud = self.get_object()

        # Obtener requisitos esperados
        if solicitud.programa_social:
            requisitos = solicitud.programa_social.requisitos_especificos.all()
        else:
            requisitos = solicitud.tramite_tipo.requisitos.all()

        # Obtener documentos subidos como diccionario para búsqueda rápida
        documentos_subidos = solicitud.documentos.all()
        documentos_por_requisito = {doc.requisito_id: doc for doc in documentos_subidos}

        # Construir respuesta detallada
        requisitos_info = []
        for req in requisitos:
            documento_info = None
            if req.id in documentos_por_requisito:
                doc = documentos_por_requisito[req.id]
                documento_info = {
                    "id": doc.id,
                    "nombre_archivo": os.path.basename(doc.archivo.name),
                    "url": doc.archivo.url if doc.archivo else None,
                    "fecha_subida": (
                        doc.fecha_subida.isoformat() if doc.fecha_subida else None
                    ),
                }

            requisitos_info.append(
                {
                    "id": req.id,
                    "nombre": req.nombre,
                    "es_obligatorio": req.es_obligatorio,
                    "requiere_documento": req.requiere_documento,
                    "documento_subido": req.id in documentos_por_requisito,
                    "documento": documento_info,
                }
            )

        completa = solicitud.verificar_documentacion_completa()

        return Response(
            {
                "documentacion_completa": completa,
                "requisitos": requisitos_info,
                "total_requisitos": len(requisitos),
                "documentos_subidos": len(documentos_subidos),
            }
        )

    @action(detail=True, methods=["get"])
    def historial(self, request, pk=None):
        """
        Obtener historial de cambios de una solicitud
        GET /api/tramites/solicitudes/{id}/historial/
        """
        solicitud = self.get_object()

        # Obtener historial de cambios ordenado por fecha descendente
        historial = solicitud.history.all().order_by("-history_date")

        # Incluir el estado actual como el primer elemento
        eventos = []

        # Agregar el estado actual
        eventos.append(
            {
                "id": solicitud.id,
                "estatus": solicitud.estatus,
                "estatus_display": solicitud.get_estatus_display(),
                "fecha": solicitud.updated_at,
                "cambio_por": "Sistema",
                "cambio_tipo": "Actualización",
                "es_actual": True,
            }
        )

        # Agregar cambios históricos
        for record in historial:
            cambio_tipo_map = {"+": "Creación", "~": "Cambio", "-": "Eliminación"}

            eventos.append(
                {
                    "id": record.id,
                    "estatus": record.estatus,
                    "estatus_display": record.get_estatus_display(),
                    "fecha": record.history_date,
                    "cambio_por": self._get_usuario_nombre(record.history_user),
                    "cambio_tipo": cambio_tipo_map.get(record.history_type, "Cambio"),
                    "es_actual": False,
                }
            )

        return Response(eventos, status=status.HTTP_200_OK)

    def _get_usuario_nombre(self, usuario):
        """Helper para obtener el nombre del usuario"""
        if not usuario:
            return "Sistema"
        try:
            if hasattr(usuario, "ciudadano"):
                ciudadano = usuario.ciudadano
                return f"{ciudadano.nombre} {ciudadano.apellido_paterno}"
            return usuario.username
        except:
            return "Sistema"

    @action(
        detail=False, methods=["get"], permission_classes=[IsAuthenticated, IsCiudadano]
    )
    def mis_solicitudes(self, request):
        """
        Endpoint para que el ciudadano vea solo sus solicitudes
        GET /api/tramites/solicitudes/mis_solicitudes/
        """
        ciudadano = request.user.ciudadano
        solicitudes = self.get_queryset().filter(ciudadano=ciudadano)

        # Aplicar filtros si existen
        estatus = request.query_params.get("estatus")
        if estatus:
            solicitudes = solicitudes.filter(estatus=estatus)

        page = self.paginate_queryset(solicitudes)
        if page is not None:
            serializer = SolicitudListSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = SolicitudListSerializer(
            solicitudes, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated, IsAdministradorOrFuncionario],
    )
    def solicitudes_asignadas(self, request):
        """
        Endpoint para que funcionarios vean solicitudes asignadas a ellos
        GET /api/tramites/solicitudes/solicitudes_asignadas/
        """
        asignaciones = SolicitudAsignacion.objects.filter(
            funcionario=request.user, activo=True
        ).values_list("solicitud_id", flat=True)

        solicitudes = self.get_queryset().filter(id__in=asignaciones)

        page = self.paginate_queryset(solicitudes)
        if page is not None:
            serializer = SolicitudListSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = SolicitudListSerializer(
            solicitudes, many=True, context={"request": request}
        )
        return Response(serializer.data)


class DocumentoSolicitudViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar documentos de solicitudes.
    """

    queryset = DocumentoSolicitud.objects.select_related("solicitud", "requisito")
    serializer_class = DocumentoSolicitudSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["solicitud", "requisito"]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return DocumentoSolicitudCreateSerializer
        return DocumentoSolicitudSerializer

    def get_queryset(self):
        """
        Filtrar documentos según el rol
        """
        queryset = super().get_queryset()
        user = self.request.user

        if user.rol == Roles.CIUDADANO:
            # Ciudadanos solo ven documentos de sus solicitudes
            queryset = queryset.filter(solicitud__ciudadano__usuario=user)

        return queryset

    def perform_create(self, serializer):
        """
        Validar que el ciudadano solo pueda subir documentos a sus propias solicitudes
        """
        solicitud = serializer.validated_data["solicitud"]

        if self.request.user.rol == Roles.CIUDADANO:
            if solicitud.ciudadano.usuario != self.request.user:
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied(
                    "No puede subir documentos a solicitudes de otros ciudadanos"
                )

        serializer.save()


class SolicitudAsignacionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar asignaciones de solicitudes a funcionarios.
    Solo accesible por administradores y funcionarios.
    """

    queryset = SolicitudAsignacion.objects.select_related(
        "solicitud", "funcionario", "dependencia", "asignado_por"
    )
    serializer_class = SolicitudAsignacionSerializer
    permission_classes = [IsAuthenticated, IsAdministradorOrFuncionario]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["solicitud", "funcionario", "dependencia", "activo"]
    ordering = ["-fecha_asignacion"]

    def perform_create(self, serializer):
        """
        Registrar quién realizó la asignación
        """
        serializer.save(asignado_por=self.request.user, es_asignacion_automatica=False)

    @action(detail=False, methods=["post"])
    def asignar_solicitud(self, request):
        """
        Endpoint para asignar una solicitud a un funcionario
        POST /api/tramites/asignaciones/asignar_solicitud/
        Body: {
            "solicitud": 1,
            "funcionario": 2,
            "dependencia": 3,
            "notas": "..."
        }
        """
        # Desactivar asignaciones anteriores para esta solicitud y dependencia
        solicitud_id = request.data.get("solicitud")
        dependencia_id = request.data.get("dependencia")

        if solicitud_id and dependencia_id:
            SolicitudAsignacion.objects.filter(
                solicitud_id=solicitud_id, dependencia_id=dependencia_id, activo=True
            ).update(activo=False)

        # Crear nueva asignación
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DashboardView(APIView):
    """
    Vista para datos del dashboard - funciona para ciudadanos y funcionarios/administradores
    - Ciudadanos: Ven solo sus propias solicitudes
    - Funcionarios/Administradores: Ven solicitudes de su dependencia
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = {
            "resumen_estatus": [],
            "total_asignadas": 0,
            "ultimas_solicitudes": [],
            "mensaje_bienvenida": "",
        }

        # Queryset base (mismo filtro que el ViewSet para consistencia)
        base_qs = Solicitud.objects.all()

        if user.rol == Roles.CIUDADANO and hasattr(user, "ciudadano"):
            # Ciudadanos ven solo sus propias solicitudes
            base_qs = base_qs.filter(ciudadano__usuario=user)
            ciudadano = user.ciudadano
            nombre = getattr(ciudadano, "nombre", user.username)
            data["mensaje_bienvenida"] = f"Bienvenido, {nombre}"
        elif user.rol == Roles.FUNCIONARIO and hasattr(user, "funcionario"):
            dependencia = user.funcionario.dependencia
            base_qs = base_qs.filter(
                Q(tramite_tipo__dependencia=dependencia)
                | Q(programa_social__dependencia=dependencia)
                | Q(asignaciones__funcionario=user, asignaciones__activo=True)
            ).distinct()
            data["mensaje_bienvenida"] = (
                f"Bienvenido, {user.funcionario.nombre_completo} ({dependencia.nombre})"
            )
        elif user.rol == Roles.ADMINISTRADOR:
            data["mensaje_bienvenida"] = "Bienvenido, Administrador"
        else:
            return Response(
                {"detail": "Rol no reconocido"}, status=status.HTTP_403_FORBIDDEN
            )

        # Conteo por estatus
        conteo = (
            base_qs.values("estatus")
            .annotate(total=Count("estatus"))
            .order_by("estatus")
        )

        # Mapear a formato amigable
        for item in conteo:
            data["resumen_estatus"].append(
                {
                    "estatus_code": item["estatus"],
                    "estatus_label": dict(EstatusSolicitud.choices).get(
                        item["estatus"], item["estatus"]
                    ),
                    "total": item["total"],
                }
            )

        # Total asignadas a MI personalmente
        if user.rol == Roles.FUNCIONARIO:
            data["total_asignadas"] = SolicitudAsignacion.objects.filter(
                funcionario=user, activo=True
            ).count()

        # Últimas 5 solicitudes
        ultimas = base_qs.order_by("-updated_at")[:5]
        data["ultimas_solicitudes"] = SolicitudListSerializer(ultimas, many=True).data

        # Return the aggregated dashboard data
        return Response(data)


from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import TruncDate
from django.db.models import Avg, F, ExpressionWrapper, DurationField
from dependencias.models import Dependencia
from usuarios.models import Usuario


class AdminDashboardViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsAdministradorOrFuncionario]

    @action(detail=False, methods=["get"])
    def stats(self, request):
        total_users = Usuario.objects.count()
        total_citizens = Usuario.objects.filter(rol=Roles.CIUDADANO).count()
        total_officials = Usuario.objects.filter(rol=Roles.FUNCIONARIO).count()

        today = timezone.now().date()
        requests_today = Solicitud.objects.filter(
            updated_at__date=today
        ).count()  # Using updated_at as proxy if created_at not avail or for activity

        active_departments = Dependencia.objects.count()

        # Avg response time: Start (created_at) to End (updated_at when status is final)
        completed_qs = Solicitud.objects.filter(
            estatus__in=[EstatusSolicitud.APROBADO, EstatusSolicitud.RECHAZADO]
        )
        # Note: If created_at is not available, we can't calculate this accurately.
        # Assuming created_at exists based on Serializer usage.
        avg_time = completed_qs.annotate(
            duration=ExpressionWrapper(
                F("updated_at") - F("created_at"), output_field=DurationField()
            )
        ).aggregate(avg=Avg("duration"))["avg"]

        avg_response_days = avg_time.days if avg_time else 0
        if avg_time:
            avg_response_days += avg_time.seconds / 86400

        status_distribution = Solicitud.objects.values("estatus").annotate(
            count=Count("estatus")
        )
        dist_dict = {item["estatus"]: item["count"] for item in status_distribution}

        data = {
            "status_distribution": dist_dict,
            "total_users": total_users,
            "total_citizens": total_citizens,
            "total_officials": total_officials,
            "requests_today": requests_today,
            "active_departments": active_departments,
            "avg_response_time_days": avg_response_days,
        }
        return Response(data)

    @action(detail=False, methods=["get"])
    def departments(self, request):
        deps = Dependencia.objects.all()
        data = []
        for dep in deps:
            qs = Solicitud.objects.filter(
                Q(tramite_tipo__dependencia=dep) | Q(programa_social__dependencia=dep)
            )
            pending = qs.filter(estatus=EstatusSolicitud.PENDIENTE).count()
            review = qs.filter(estatus=EstatusSolicitud.EN_REVISION).count()

            data.append(
                {
                    "id": dep.id,
                    "nombre": dep.nombre,
                    "pending_count": pending,
                    "in_review_count": review,
                }
            )
        return Response(data)

    @action(detail=False, methods=["get"])
    def trends(self, request):
        period = request.query_params.get("period", "30days")
        days = 30
        if period == "7days":
            days = 7
        elif period == "90days":
            days = 90

        start_date = timezone.now() - timedelta(days=days)

        qs = Solicitud.objects.filter(created_at__gte=start_date)

        by_date = (
            qs.annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(
                created=Count("id"),
                approved=Count("id", filter=Q(estatus=EstatusSolicitud.APROBADO)),
                rejected=Count("id", filter=Q(estatus=EstatusSolicitud.RECHAZADO)),
            )
            .order_by("date")
        )

        labels = []
        created = []
        approved = []
        rejected = []

        for item in by_date:
            labels.append(item["date"].strftime("%Y-%m-%d"))
            created.append(item["created"])
            approved.append(item["approved"])
            rejected.append(item["rejected"])

        return Response(
            {
                "labels": labels,
                "requests_created": created,
                "requests_approved": approved,
                "requests_rejected": rejected,
            }
        )

    @action(detail=False, methods=["get"])
    def requests(self, request):
        qs = Solicitud.objects.all().select_related(
            "ciudadano", "tramite_tipo", "programa_social"
        )

        search = request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(id__icontains=search)
                | Q(ciudadano__nombre__icontains=search)
                | Q(descripcion_ciudadano__icontains=search)
            )

        status_filter = request.query_params.get("status")
        if status_filter and status_filter != "undefined":
            qs = qs.filter(estatus=status_filter)

        dept_filter = request.query_params.get("department")
        if dept_filter and dept_filter != "undefined":
            qs = qs.filter(
                Q(tramite_tipo__dependencia_id=dept_filter)
                | Q(programa_social__dependencia_id=dept_filter)
            )

        paginator = SolicitudViewSet().paginator  # Reuse paginator?
        # APIView doesn't have paginator. ViewSet does but it's not initialized same way.
        # Just use DRF pagination manually or via ViewSet features.

        # AdminDashboardViewSet is a ViewSet, not ModelViewSet, so it doesn't have pagination_class set by default
        # unless configured in settings or specified.
        # Let's import standard pagination.
        from rest_framework.pagination import PageNumberPagination

        paginator = PageNumberPagination()
        paginator.page_size = 20

        page = paginator.paginate_queryset(qs, request)
        if page is not None:
            serializer = SolicitudListSerializer(
                page, many=True, context={"request": request}
            )
            return paginator.get_paginated_response(serializer.data)

        serializer = SolicitudListSerializer(
            qs, many=True, context={"request": request}
        )
        return Response(serializer.data)
