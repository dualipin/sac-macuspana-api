import django_filters
from apoyos.models import ProgramaSocial


class ProgramaSocialFilter(django_filters.FilterSet):
    nombre = django_filters.CharFilter(lookup_expr='icontains')
    descripcion = django_filters.CharFilter(lookup_expr='icontains')
    destacado = django_filters.BooleanFilter()
    
    class Meta:
        model = ProgramaSocial
        fields = ['dependencia', 'esta_activo', 'destacado', 'categoria']
