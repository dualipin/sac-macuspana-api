import pandas as pd
from django.core.management.base import BaseCommand
from django.db import connection
from localidades.models import Localidad


class Command(BaseCommand):
    help = 'Carga optimizada de localidades (Compatible con SQLite y Postgres)'

    def add_arguments(self, parser):
        parser.add_argument('ruta', type=str)

    def handle(self, *args, **options):
        # 1. Detección de motor para evitar errores en SQLite
        # SQLite tiene un límite de 999 variables por consulta
        vendor = connection.vendor
        batch_size = 900 if vendor == 'sqlite' else 5000

        self.stdout.write(f"Detectado motor: {vendor}. Usando batch_size: {batch_size}")

        # 2. Lectura selectiva del CSV
        cols_sepomex = ['d_codigo', 'd_asenta', 'd_tipo_asenta', 'D_mnpio', 'd_estado']
        df = pd.read_csv(
            options['ruta'],
            encoding='latin1',
            sep='|',
            dtype=str,
            usecols=cols_sepomex
        )

        df = df[['d_codigo', 'd_asenta', 'D_mnpio', 'd_estado', 'd_tipo_asenta']]

        df.columns = ['codigo_postal', 'colonia', 'municipio', 'estado', 'tipo']
        # df = df.drop_duplicates()

        # 3. Limpieza atómica (Más segura)
        Localidad.objects.all().delete()

        # 4. Generador para no saturar la RAM
        def localidad_generator():
            for row in df.itertuples(index=False):
                yield Localidad(
                    codigo_postal=row.codigo_postal,
                    colonia=row.colonia,
                    municipio=row.municipio,
                    estado=row.estado,
                    tipo=row.tipo
                )

        # 5. Inserción masiva
        Localidad.objects.bulk_create(
            localidad_generator(),
            batch_size=batch_size,
            ignore_conflicts=True
        )

        self.stdout.write(self.style.SUCCESS(f'✅ {len(df)} registros procesados.'))
