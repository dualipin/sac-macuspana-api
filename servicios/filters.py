import django_filters
from .models import TramiteCatalogo, TipoTramites


class TramiteCatalogoFilter(django_filters.FilterSet):
    nombre = django_filters.CharFilter(lookup_expr='icontains')
    dependencia = django_filters.NumberFilter(field_name='dependencia__id')

    # Nuevo filtro personalizado para el nombre legible
    tipo = django_filters.CharFilter(method='filter_por_nombre_legible')

    destacado = django_filters.BooleanFilter()
    
    class Meta:
        model = TramiteCatalogo
        fields = ['nombre', 'dependencia', 'destacado']

    def filter_por_nombre_legible(self, queryset, name, value):
        # .label es la etiqueta legible de cada miembro del Enum
        mapa_nombres = {choice.label.lower(): choice.value for choice in TipoTramites}

        clave_db = mapa_nombres.get(value.lower())

        if clave_db:
            return queryset.filter(tipo=clave_db)

        # Si no hay coincidencia, devolvemos el queryset vacío para que no traiga basura
        return queryset.none()
