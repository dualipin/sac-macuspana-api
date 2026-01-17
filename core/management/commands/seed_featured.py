from django.core.management.base import BaseCommand
from servicios.models import TramiteCatalogo, TipoTramites
from dependencias.models import Dependencia
from apoyos.models import ProgramaSocial


class Command(BaseCommand):
    help = 'Seed featured procedures and programs'

    def handle(self, *args, **options):
        # Ensure a dependency exists
        dep, _ = Dependencia.objects.get_or_create(
            siglas="TES",
            defaults={
                "nombre": "Tesorería Municipal",
            }
        )

        # Create or update a featured procedure
        t1, created = TramiteCatalogo.objects.get_or_create(
            nombre="Pago de Predial (Test)",
            defaults={
                "dependencia": dep,
                "descripcion": "Consulta y realiza el pago de tu impuesto predial en línea.",
                "tipo": TipoTramites.SOLICITUD_GENERAL,
            }
        )
        t1.destacado = True
        t1.save()

        t2, created = TramiteCatalogo.objects.get_or_create(
            nombre="Actas de Nacimiento (Test)",
            defaults={
                "dependencia": dep,
                "descripcion": "Solicita copias certificadas.",
                "tipo": TipoTramites.SOLICITUD_GENERAL,
            }
        )
        t2.destacado = True
        t2.save()

        self.stdout.write(
            self.style.SUCCESS(f"Seeded: {t1.nombre} and {t2.nombre} as featured.")
        )

        p1, created = ProgramaSocial.objects.get_or_create(
            nombre="Apoyo al Adulto Mayor",
            defaults={
                "dependencia": dep,
                "descripcion": "Programas de asistencia para adultos mayores.",
                "categoria": "Bienestar Social"
            }
        )
        p1.destacado = True
        p1.save()

        p2, created = ProgramaSocial.objects.get_or_create(
            nombre="Becas Estudiantiles",
            defaults={
                "dependencia": dep,
                "descripcion": "Apoyo para estudiantes destacados.",
                "categoria": "Educación"
            }
        )
        p2.destacado = True
        p2.save()

        self.stdout.write(
            self.style.SUCCESS(f"Seeded programs: {p1.nombre} and {p2.nombre}")
        )
