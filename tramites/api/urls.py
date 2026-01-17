from django.urls import path, include
from rest_framework import routers

from .views import (
    SolicitudViewSet,
    DocumentoSolicitudViewSet,
    SolicitudAsignacionViewSet,
    SolicitudAsignacionViewSet,
    DashboardView,
    AdminDashboardViewSet,
)

router = routers.DefaultRouter()
router.register("solicitudes", SolicitudViewSet)
router.register("documentos", DocumentoSolicitudViewSet)
router.register("asignaciones", SolicitudAsignacionViewSet)
# No need to register ViewSet with actions in router if we map manually or use proper ViewSet structure for router
# But for custom non-model viewset, actions can be mapped manually is often easier or register as basename
router.register("dashboard/admin", AdminDashboardViewSet, basename="admin-dashboard")

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard-resumen"),
    path("", include(router.urls)),
]
