from django.core.management.base import BaseCommand
from django.db import transaction
from dependencias.models import Dependencia
from servicios.models import TramiteCatalogo, Requisito
from apoyos.models import ProgramaSocial
from core.choices import TipoTramites, TipoDependencia

class Command(BaseCommand):
    help = 'Pobla la base de datos con catálogos esenciales para escenarios de demostración usando dependencias reales'

    def handle(self, *args, **kwargs):
        self.stdout.write('Iniciando proceso de sembrado de datos...')

        with transaction.atomic():
            # 1. Mapeo de dependencias requeridas usando los nombres EXACTOS del CSV
            # CSV ID 13: DIRECCIÓN DE ATENCION CIUDADANA
            # CSV ID 25: COORD. DE TRANSPARENCIA 
            # CSV ID 8: DIRECCIÓN DE OBRAS, ORDENAMIENTO TERRITORIAL Y SERVICIOS MUNICIPALES
            # CSV ID 23: COORD. DEL DIF

            deps_config = {
                'atencion': {
                    'nombre': 'DIRECCIÓN DE ATENCION CIUDADANA',
                    'tipo': TipoDependencia.DIRECCION,
                    'defaults': {} 
                },
                'transparencia': {
                    'nombre': 'COORD. DE TRANSPARENCIA ', # Nota: El CSV tiene un espacio al final
                    'tipo': TipoDependencia.COORDINACION,
                    'defaults': {}
                },
                'servicios': {
                    'nombre': 'DIRECCIÓN DE OBRAS, ORDENAMIENTO TERRITORIAL Y SERVICIOS MUNICIPALES',
                    'tipo': TipoDependencia.DIRECCION,
                    'defaults': {}
                },
                'dif': {
                    'nombre': 'COORD. DEL DIF',
                    'tipo': TipoDependencia.COORDINACION,
                    'defaults': {'siglas': 'DIF'}
                }
            }

            dependencias = {}
            for key, config in deps_config.items():
                # Buscamos o creamos, pero asumiendo que el seed principal de dependencias ya corrió o lo creamos aquí
                defaults = {'tipo': config['tipo']}
                defaults.update(config['defaults'])
                
                dep, created = Dependencia.objects.get_or_create(
                    nombre=config['nombre'],
                    defaults=defaults
                )
                dependencias[key] = dep
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Dependencia creada: {dep.nombre}'))
                else:
                    self.stdout.write(f'Dependencia encontrada: {dep.nombre}')

            # 2. Crear Trámites Catalogo vinculados a las dependencias reales
            tramites_data = [
                {
                    'nombre': 'Atención Ciudadana y Dudas',
                    'dependencia': dependencias['atencion'],
                    'tipo': TipoTramites.SOLICITUD_GENERAL,
                    'descripcion': 'Canal para dudas generales, quejas simples o solicitudes que no tienen un trámite específico. Su solicitud será canalizada al área correspondiente.',
                    'requisitos': [] 
                },
                {
                    'nombre': 'Solicitud de Acceso a la Información',
                    'dependencia': dependencias['transparencia'],
                    'tipo': TipoTramites.TRAMITE_ADMINISTRATIVO,
                    'descripcion': 'Solicitud formal de información pública gubernamental según la ley de transparencia.',
                    'requisitos': [
                        {'nombre': 'Identificación Oficial', 'es_obligatorio': True, 'requiere_documento': True}
                    ]
                },
                {
                    'nombre': 'Reporte de Alumbrado Público',
                    'dependencia': dependencias['servicios'],
                    'tipo': TipoTramites.SOLICITUD_GENERAL,
                    'descripcion': 'Reporte de fallas en luminarias o falta de iluminación en calles y parques.',
                    'requisitos': [
                        {'nombre': 'Evidencia Fotográfica', 'es_obligatorio': False, 'requiere_documento': True},
                        {'nombre': 'Ubicación Exacta (Referencia)', 'es_obligatorio': True, 'requiere_documento': False}
                    ]
                }
            ]

            for tramite_info in tramites_data:
                tramite, created = TramiteCatalogo.objects.get_or_create(
                    nombre=tramite_info['nombre'],
                    defaults={
                        'dependencia': tramite_info['dependencia'],
                        'tipo': tramite_info['tipo'],
                        'descripcion': tramite_info['descripcion'],
                        # 'empieza_activo': True # Removed as it doesn't exist in model
                    }
                )
                
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Trámite creado: {tramite.nombre}'))
                    for req_info in tramite_info['requisitos']:
                        Requisito.objects.create(
                            tramite=tramite,
                            nombre=req_info['nombre'],
                            es_obligatorio=req_info['es_obligatorio'],
                            requiere_documento=req_info['requiere_documento']
                        )
                else:
                    # Optional: Update dependency if it was wrong before (e.g. from previous bad seed)
                    if tramite.dependencia != tramite_info['dependencia']:
                        tramite.dependencia = tramite_info['dependencia']
                        tramite.save()
                        self.stdout.write(self.style.WARNING(f'Trámite actualizado con dependencia correcta: {tramite.nombre}'))
                    else:
                        self.stdout.write(f'Trámite ya existente: {tramite.nombre}')

            # 3. Crear Programa Social
            dif_dep = dependencias['dif']
            prog_lentes, created = ProgramaSocial.objects.get_or_create(
                nombre='Programa de Lentes a Bajo Costo',
                defaults={
                    'dependencia': dif_dep,
                    'descripcion': 'Apoyo para la adquisición de lentes graduados a bajo costo para personas de escasos recursos.',
                    'categoria': 'Salud y Bienestar',
                    'destacado': True,
                    'esta_activo': True
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Programa creado: {prog_lentes.nombre}'))
                Requisito.objects.create(
                    programa=prog_lentes,
                    nombre='Identificación Oficial (INE)',
                    es_obligatorio=True,
                    requiere_documento=True
                )
                Requisito.objects.create(
                    programa=prog_lentes,
                    nombre='CURP',
                    es_obligatorio=True,
                    requiere_documento=True
                )
                Requisito.objects.create(
                    programa=prog_lentes,
                    nombre='Receta Médica (Opcional)',
                    es_obligatorio=False,
                    requiere_documento=True
                )
            else:
                if prog_lentes.dependencia != dif_dep:
                    prog_lentes.dependencia = dif_dep
                    prog_lentes.save()
                    self.stdout.write(self.style.WARNING(f'Programa actualizado con dependencia correcta: {prog_lentes.nombre}'))
                else:
                    self.stdout.write(f'Programa ya existente: {prog_lentes.nombre}')

        self.stdout.write(self.style.SUCCESS('Proceso de sembrado completado exitosamente con dependencias reales.'))
