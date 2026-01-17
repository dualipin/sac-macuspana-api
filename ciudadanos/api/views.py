from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from ciudadanos.api.serializers import RegistroCiudadanoSerializer
from rest_framework import generics, filters
from ciudadanos.models import Ciudadano
from ciudadanos.validators.curp import validate_curp_format, check_curp_unica
from django.db.models import Q
import hashlib


class CiudadanoCreateView(generics.CreateAPIView):
    serializer_class = RegistroCiudadanoSerializer
    queryset = Ciudadano.objects.all()


@api_view(['POST'])
@throttle_classes([AnonRateThrottle])  # Límite de 5/min en settings
def verificar_curp_view(request):
    curp_input = request.data.get('curp', '')

    try:
        # Validaciones locales (Costo 0)
        validate_curp_format(curp_input)
        check_curp_unica(curp_input)

        return Response(status=204)

    except Exception as e:
        print(e)
        return Response(status=400)
#
#
# @api_view(['POST'])
# def paso2_registrar_ciudadano(request):
#     token = request.data.get('session_token')
#     temp_data = cache.get(f"reg_{token}")
#
#     if not temp_data:
#         return Response({"error": "La sesión expiró o es inválida."}, status=400)
#
#     serializer = RegistroCiudadanoSerializer(data=request.data)
#
#     if serializer.is_valid():
#         password = serializer.validated_data.pop('password')  # Extraemos la contraseña válida
#
#         try:
#             with transaction.atomic():
#                 # 1. Crear el Usuario con la contraseña recibida
#                 nuevo_usuario = Usuario.objects.create_user(
#                     username=temp_data['curp'],
#                     password=password,
#                     rol=Roles.CIUDADANO
#                 )
#
#                 # 2. Crear el Ciudadano
#                 api = temp_data['api_data']
#                 serializer.save(
#                     usuario=nuevo_usuario,
#                     curp=temp_data['curp'],
#                     nombre=api['nombres'],
#                     apellido_paterno=api['apellido_paterno'],
#                     apellido_materno=api.get('apellido_materno'),
#                     fecha_nacimiento=parsear_fecha(api['fecha_nacimiento']),
#                     sexo='M' if api['sexo'] == 'MUJER' else 'H'
#                 )
#
#             cache.delete(f"reg_{token}")
#             return Response({"status": "Ciudadano creado correctamente"}, status=201)
#
#         except Exception as e:
#             print(e)
#             return Response({"error": "Error crítico en el registro."}, status=500)
#
#     return Response(serializer.errors, status=400)


from rest_framework import generics, filters
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from ciudadanos.api.serializers import CiudadanoSerializer, CiudadanoUpdateSerializer

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class CiudadanoListView(generics.ListAPIView):
    queryset = Ciudadano.objects.all().order_by('-id')
    serializer_class = CiudadanoSerializer
    permission_classes = [IsAuthenticated] # TODO: Add IsAdminUser
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Ciudadano.objects.all().order_by('-id')
        search = self.request.query_params.get('search', '')
        
        if search:
            # Crear hashes para búsquedas de campos encriptados
            curp_hash = hashlib.sha256(search.upper().encode()).hexdigest()
            email_hash = hashlib.sha256(search.lower().encode()).hexdigest()
            
            queryset = queryset.filter(
                Q(nombre__icontains=search) |
                Q(apellido_paterno__icontains=search) |
                Q(apellido_materno__icontains=search) |
                Q(curp_hash=curp_hash) |
                Q(correo_hash=email_hash) |
                Q(telefono__icontains=search)
            )
        
        return queryset


class CiudadanoUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Ciudadano.objects.all()
    serializer_class = CiudadanoSerializer
    permission_classes = [IsAuthenticated] # TODO: Add IsAdminUser

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return CiudadanoUpdateSerializer
        return CiudadanoSerializer


from rest_framework.decorators import action
from rest_framework import status
from ciudadanos.api.serializers import CiudadanoDireccionUpdateSerializer
from rest_framework import viewsets


class CiudadanoDireccionUpdateView(generics.UpdateAPIView):
    """Vista para actualizar solo la dirección del ciudadano"""
    queryset = Ciudadano.objects.all()
    serializer_class = CiudadanoDireccionUpdateSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['patch', 'put']

    def get_object(self):
        """Obtener el ciudadano del usuario autenticado"""
        return self.request.user.ciudadano
