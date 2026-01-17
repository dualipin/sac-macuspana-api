from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from dependencias.models import Dependencia, Funcionario
from .serializers import DependenciaSerializer, FuncionarioSerializer

class DependenciaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar dependencias.
    Soporta CRUD completo.
    """
    queryset = Dependencia.objects.all()
    serializer_class = DependenciaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['tipo']
    search_fields = ['nombre', 'siglas', 'tipo']

class FuncionarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar funcionarios.
    Soporta paginación, filtrado y búsqueda.
    
    Filtros disponibles:
    - ?search=<texto> - Busca en nombre_completo y correo
    - ?dependencia=<id> - Filtra por dependencia
    - ?cargo=<cargo> - Filtra por cargo
    - ?sexo=<sexo> - Filtra por sexo (M, F, O)
    - ?ordering=<campo> - Ordena por nombre_completo o cargo
    """
    queryset = Funcionario.objects.all()
    serializer_class = FuncionarioSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['dependencia', 'cargo', 'sexo']
    search_fields = ['nombre_completo', 'correo']
    ordering_fields = ['nombre_completo', 'cargo']
    ordering = ['nombre_completo']