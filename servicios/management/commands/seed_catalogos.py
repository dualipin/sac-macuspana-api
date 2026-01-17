from django.core.management.base import BaseCommand
from django.db import transaction
from dependencias.models import Dependencia
from apoyos.models import ProgramaSocial
from servicios.models import TramiteCatalogo, Requisito
from core.choices import TipoTramites


class Command(BaseCommand):
    help = 'Puebla el catálogo de trámites, programas sociales y sus requisitos para pruebas'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Iniciando carga de catálogos de prueba...'))

        with transaction.atomic():
            # 1. Obtener dependencias necesarias (basadas en tu importación previa)
            # Usamos get_or_create por si acaso, pero idealmente ya existen
            def_finanzas, _ = Dependencia.objects.get_or_create(nombre="DIRECCIÓN DE FINANZAS")
            def_sapam, _ = Dependencia.objects.get_or_create(
                nombre="DIRECCIÓN DEL SISTEMA DE AGUA POTABLE Y ALCANTARILLADO DE MACUSPANA", siglas="SAPAM")
            def_obras, _ = Dependencia.objects.get_or_create(
                nombre="DIRECCIÓN DE OBRAS, ORDENAMIENTO TERRITORIAL Y SERVICIOS MUNICIPALES")
            def_vivienda, _ = Dependencia.objects.get_or_create(
                nombre="DIRECCION DEL INSTITUTO DE VIVIENDA DE MACUSPANA")
            def_educacion, _ = Dependencia.objects.get_or_create(nombre="DIRECCION DEL EDUCACION CULTURA Y RECREACION")
            def_atencion, _ = Dependencia.objects.get_or_create(nombre="DIRECCIÓN DE ATENCION CIUDADANA")

            # 2. Crear Trámites de Ejemplo (Servicios Generales y Administrativos)
            # Estos representan los "40 tipos de solicitudes" mencionados en el anteproyecto [cite: 78]
            tramites_data = [
                (def_sapam, "Pago de Derechos de Agua", TipoTramites.TRAMITE_ADMINISTRATIVO,
                 "Trámite para el pago bimestral o anual del servicio de agua potable."),
                (def_sapam, "Reporte de Fuga de Agua", TipoTramites.SOLICITUD_GENERAL,
                 "Reporte de fugas en la red pública de Macuspana."),
                (def_finanzas, "Pago de Impuesto Predial", TipoTramites.TRAMITE_ADMINISTRATIVO,
                 "Cumplimiento de la obligación fiscal sobre bienes inmuebles."),
                (def_obras, "Solicitud de Bacheo", TipoTramites.SOLICITUD_GENERAL,
                 "Petición para la reparación de baches en calles y avenidas."),
                (def_obras, "Reparación de Luminarias", TipoTramites.SOLICITUD_GENERAL,
                 "Reporte de fallas en el alumbrado público municipal."),
            ]

            for dep, nombre, tipo, desc in tramites_data:
                tramite = TramiteCatalogo.objects.create(
                    dependencia=dep,
                    nombre=nombre,
                    tipo=tipo,
                    descripcion=desc
                )
                # Requisito base para todos los trámites
                Requisito.objects.create(
                    tramite=tramite,
                    nombre="Identificación Oficial (INE)",
                    es_obligatorio=True,
                    requiere_documento=True
                )

            # 3. Crear Programas Sociales de Ejemplo
            # Esto cubre parte de los "30 programas" definidos en la justificación [cite: 78]
            programas_data = [
                (def_vivienda, "Programa de Láminas de Zinc",
                 "Apoyo para el mejoramiento de techumbres en viviendas vulnerables."),
                (def_vivienda, "Construcción de Piso Firme", "Sustitución de pisos de tierra por concreto hidráulico."),
                (def_educacion, "Becas Municipales de Excelencia",
                 "Apoyo económico para estudiantes de alto desempeño académico."),
                (def_vivienda, "Programa Pies de Casa",
                 "Construcción de un cuarto dormitorio básico para familias en hacinamiento."),
                (def_atencion, "Apoyo para Gastos Funerarios",
                 "Asistencia económica para familias de escasos recursos."),
            ]

            # Creamos un trámite "contenedor" base para solicitudes de apoyo
            tramite_apoyo_base = TramiteCatalogo.objects.create(
                dependencia=def_atencion,
                nombre="Solicitud de Apoyo Social",
                tipo=TipoTramites.APOYO_SOCIAL,
                descripcion="Trámite general para aplicar a cualquier programa social del ayuntamiento."
            )

            for dep, nombre, desc in programas_data:
                prog = ProgramaSocial.objects.create(
                    dependencia=dep,
                    nombre=nombre,
                    descripcion=desc,
                    esta_activo=True
                )

                # Requisitos dinámicos (Opción B): vinculados al trámite base Y al programa específico
                # Requisito común para todos los programas
                Requisito.objects.create(
                    tramite=tramite_apoyo_base,
                    programa=prog,
                    nombre="CURP Actualizada",
                    es_obligatorio=True,
                    requiere_documento=True
                )

                # Requisito específico según el programa
                if "Láminas" in nombre or "Pies de Casa" in nombre:
                    Requisito.objects.create(
                        tramite=tramite_apoyo_base,
                        programa=prog,
                        nombre="Fotografías de la Vivienda (Evidencia)",
                        es_obligatorio=True,
                        requiere_documento=True
                    )

                if "Becas" in nombre:
                    Requisito.objects.create(
                        tramite=tramite_apoyo_base,
                        programa=prog,
                        nombre="Constancia de Estudios Vigente",
                        es_obligatorio=True,
                        requiere_documento=True
                    )

        self.stdout.write(self.style.SUCCESS('Catálogo de trámites y programas sociales cargado exitosamente.'))
