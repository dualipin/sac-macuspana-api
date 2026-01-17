from django.core.management.base import BaseCommand
from django.db import transaction
from dependencias.models import Dependencia, Funcionario
from servicios.models import TramiteCatalogo, Requisito
from apoyos.models import ProgramaSocial
from core.choices import TipoTramites, TipoDependencia

class Command(BaseCommand):
    help = 'Pobla la base de datos con catálogos de prueba (Trámites, Requisitos, etc.)'

    def handle(self, *args, **kwargs):
        self.stdout.write("Iniciando seed de catálogos...")

        try:
            with transaction.atomic():
                self._crear_dependencias_core()
                self._crear_tramites_comunes()
                self._crear_programas_sociales()
                self.stdout.write(self.style.SUCCESS("¡Base de datos poblada exitosamente!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error al poblar BD: {str(e)}"))

    def _crear_dependencias_core(self):
        deptos = [
            {"nombre": "Secretaría del Ayuntamiento", "siglas": "SEC"},
            {"nombre": "Obras Públicas", "siglas": "DOP"},
            {"nombre": "Registro Civil", "siglas": "RC"},
            {"nombre": "Sistema de Agua y Saneamiento", "siglas": "SAPAM"},
            {"nombre": "Atención Ciudadana", "siglas": "UAC"},
        ]
        
        for d in deptos:
            Dependencia.objects.get_or_create(
                nombre=d["nombre"],
                defaults={"siglas": d["siglas"], "tipo": TipoDependencia.DEPARTAMENTO}
            )

    def _crear_tramites_comunes(self):
        # 1. Pago de Agua (SAPAM)
        sapam = Dependencia.objects.get(nombre="Sistema de Agua y Saneamiento")
        tramite_agua, _ = TramiteCatalogo.objects.get_or_create(
            nombre="Pago de Agua Potable",
            dependencia=sapam,
            defaults={
                "descripcion": "Pago bimestral del servicio de agua potable.",
                "tipo": TipoTramites.PAGO_IMPUESTO
            }
        )
        
        Requisito.objects.get_or_create(
            tramite=tramite_agua, nombre="Recibo anterior", 
            defaults={"es_obligatorio": False, "requiere_documento": True}
        )
        Requisito.objects.get_or_create(
            tramite=tramite_agua, nombre="Comprobante de Pago (Transferencia)", 
            defaults={"es_obligatorio": True, "requiere_documento": True}
        )

        # 2. Acta de Nacimiento (Registro Civil)
        rc = Dependencia.objects.get(nombre="Registro Civil")
        tramite_acta, _ = TramiteCatalogo.objects.get_or_create(
            nombre="Copia Certificada de Acta de Nacimiento",
            dependencia=rc,
            defaults={
                "descripcion": "Solicitud de copia certificada de acta de nacimiento.",
                "tipo": TipoTramites.SOLICITUD_NO_PRESENCIAL
            }
        )
        
        Requisito.objects.get_or_create(
            tramite=tramite_acta, nombre="CURP", 
            defaults={"es_obligatorio": True, "requiere_documento": True}
        )
        Requisito.objects.get_or_create(
            tramite=tramite_acta, nombre="Identificación Oficial (INE)", 
            defaults={"es_obligatorio": True, "requiere_documento": True}
        )

    def _crear_programas_sociales(self):
        # 1. Apoyo Alimentario
        dif_nombre = "DIF Municipal"  # Asumiendo que se crea o existe, si no lo creamos on the fly
        dif, _ = Dependencia.objects.get_or_create(nombre=dif_nombre, defaults={"siglas": "DIF"})
        
        prog_despensas, _ = ProgramaSocial.objects.get_or_create(
            nombre="Programa de Apoyo Alimentario",
            dependencia=dif,
            defaults={
                "descripcion": "Entrega de despensas a familias vulnerables.",
                "esta_activo": True
            }
        )
        
        Requisito.objects.get_or_create(
            programa=prog_despensas, nombre="Estudio Socioeconómico", 
            defaults={"es_obligatorio": True, "requiere_documento": True}
        )
        Requisito.objects.get_or_create(
            programa=prog_despensas, nombre="Comprobante de Domicilio", 
            defaults={"es_obligatorio": True, "requiere_documento": True}
        )
