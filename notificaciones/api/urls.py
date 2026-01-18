from django.urls import path
from .views import (
    NotificacionListView,
    NotificacionNoLeidasView,
    NotificacionNoLeidasCountView,
    NotificacionMarcarLeidaView,
    NotificacionMarcarTodasLeidasView,
)

urlpatterns = [
    path("", NotificacionListView.as_view(), name="notificaciones-list"),
    path(
        "no_leidas/",
        NotificacionNoLeidasView.as_view(),
        name="notificaciones-no-leidas",
    ),
    path(
        "no_leidas_count/",
        NotificacionNoLeidasCountView.as_view(),
        name="notificaciones-no-leidas-count",
    ),
    path(
        "<int:pk>/marcar_como_leida/",
        NotificacionMarcarLeidaView.as_view(),
        name="notificacion-marcar-leida",
    ),
    path(
        "marcar_todas_como_leidas/",
        NotificacionMarcarTodasLeidasView.as_view(),
        name="notificaciones-marcar-todas-leidas",
    ),
]
