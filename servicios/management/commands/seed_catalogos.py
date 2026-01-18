from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from core.choices import TipoTramites, TipoDependencia
from dependencias.models import Dependencia
from servicios.models import TramiteCatalogo, Requisito


class Command(BaseCommand):
    help = "Pobla la base de datos con catálogos esenciales para escenarios de demostración usando dependencias reales"

    def handle(self, *args, **kwargs):
        self.stdout.write("Iniciando proceso de sembrado de datos...")

        with transaction.atomic():
            # 1. Mapeo de dependencias requeridas usando los nombres EXACTOS del CSV
            # CSV ID 13: DIRECCIÓN DE ATENCION CIUDADANA
            # CSV ID 25: COORD. DE TRANSPARENCIA
            # CSV ID 8: DIRECCIÓN DE OBRAS, ORDENAMIENTO TERRITORIAL Y SERVICIOS MUNICIPALES
            # CSV ID 23: COORD. DEL DIF

            deps_config = {
                "atencion": {
                    "nombre": "DIRECCIÓN DE ATENCION CIUDADANA",
                    "tipo": TipoDependencia.DIRECCION,
                    "defaults": {},
                },
                "transparencia": {
                    "nombre": "COORD. DE TRANSPARENCIA ",  # Nota: El CSV tiene un espacio al final
                    "tipo": TipoDependencia.COORDINACION,
                    "defaults": {},
                },
                "servicios": {
                    "nombre": "DIRECCIÓN DE OBRAS, ORDENAMIENTO TERRITORIAL Y SERVICIOS MUNICIPALES",
                    "tipo": TipoDependencia.DIRECCION,
                    "defaults": {},
                },
            }

            dependencias = {}
            for key, config in deps_config.items():
                # Buscamos o creamos, pero asumiendo que el seed principal de dependencias ya corrió o lo creamos aquí
                defaults = {"tipo": config["tipo"]}
                defaults.update(config["defaults"])

                dep, created = Dependencia.objects.get_or_create(
                    nombre=config["nombre"], defaults=defaults
                )
                dependencias[key] = dep
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f"Dependencia creada: {dep.nombre}")
                    )
                else:
                    self.stdout.write(f"Dependencia encontrada: {dep.nombre}")

            assets_dir = Path(settings.BASE_DIR) / "data" / "assets"
            imagenes_tramites = {
                "Atención Ciudadana y Dudas": "atencion-ciudadana-dudas.png",
                "Solicitud de Acceso a la Información": "solicitud-informacion.png",
            }

            # 2. Crear Trámites Catalogo vinculados a las dependencias reales
            tramites_data = [
                {
                    "nombre": "Atención Ciudadana y Dudas",
                    "dependencia": dependencias["atencion"],
                    "tipo": TipoTramites.SOLICITUD_GENERAL,
                    "descripcion": "Canal para dudas generales, quejas simples o solicitudes que no tienen un trámite específico. Su solicitud será canalizada al área correspondiente.",
                    "destacado": True,
                    "requisitos": [],
                },
                {
                    "nombre": "Solicitud de Acceso a la Información",
                    "dependencia": dependencias["transparencia"],
                    "tipo": TipoTramites.TRAMITE_ADMINISTRATIVO,
                    "descripcion": "Solicitud formal de información pública gubernamental según la ley de transparencia.",
                    "destacado": True,
                    "requisitos": [
                        {
                            "nombre": "Identificación Oficial",
                            "es_obligatorio": True,
                            "requiere_documento": True,
                        }
                    ],
                },
            ]

            for tramite_info in tramites_data:
                tramite, created = TramiteCatalogo.objects.get_or_create(
                    nombre=tramite_info["nombre"],
                    defaults={
                        "dependencia": tramite_info["dependencia"],
                        "tipo": tramite_info["tipo"],
                        "descripcion": tramite_info["descripcion"],
                        "destacado": tramite_info["destacado"],
                    },
                )

                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f"Trámite creado: {tramite.nombre}")
                    )
                    for req_info in tramite_info["requisitos"]:
                        Requisito.objects.create(
                            tramite=tramite,
                            nombre=req_info["nombre"],
                            es_obligatorio=req_info["es_obligatorio"],
                            requiere_documento=req_info["requiere_documento"],
                        )
                else:
                    # Optional: Update dependency if it was wrong before (e.g. from previous bad seed)
                    if tramite.dependencia != tramite_info["dependencia"]:
                        tramite.dependencia = tramite_info["dependencia"]
                        tramite.save()
                        self.stdout.write(
                            self.style.WARNING(
                                f"Trámite actualizado con dependencia correcta: {tramite.nombre}"
                            )
                        )
                    else:
                        self.stdout.write(f"Trámite ya existente: {tramite.nombre}")

                asset_filename = imagenes_tramites.get(tramite.nombre)
                if asset_filename:
                    asset_path = assets_dir / asset_filename
                    if asset_path.exists() and not tramite.imagen:
                        with asset_path.open("rb") as image_file:
                            tramite.imagen.save(
                                asset_filename, File(image_file), save=True
                            )
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Imagen asociada a trámite: {tramite.nombre}"
                            )
                        )
                    elif not asset_path.exists():
                        self.stdout.write(
                            self.style.WARNING(
                                f"Imagen no encontrada para {tramite.nombre}: {asset_path}"
                            )
                        )

        self.stdout.write(
            self.style.SUCCESS(
                "Proceso de sembrado completado exitosamente con dependencias reales."
            )
        )
