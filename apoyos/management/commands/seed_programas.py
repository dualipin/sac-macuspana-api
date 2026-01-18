from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from apoyos.models import ProgramaSocial
from core.choices import TipoDependencia
from dependencias.models import Dependencia
from servicios.models import Requisito


class Command(BaseCommand):
    help = "Siembra programas sociales con sus imágenes"

    def handle(self, *args, **kwargs):
        self.stdout.write("Iniciando proceso de sembrado de programas sociales...")

        with transaction.atomic():
            # Obtener o crear las dependencias
            dep_finanzas, created = Dependencia.objects.get_or_create(
                nombre="DIRECCIÓN DE FINANZAS",
                defaults={"tipo": TipoDependencia.DIRECCION},
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Dependencia creada: {dep_finanzas.nombre}")
                )
            else:
                self.stdout.write(f"Dependencia encontrada: {dep_finanzas.nombre}")

            dep_mujeres, created = Dependencia.objects.get_or_create(
                nombre="DIRECCIÓN DE ATENCION A LAS MUJERES",
                defaults={"tipo": TipoDependencia.DIRECCION},
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Dependencia creada: {dep_mujeres.nombre}")
                )
            else:
                self.stdout.write(f"Dependencia encontrada: {dep_mujeres.nombre}")

            dep_vivienda, created = Dependencia.objects.get_or_create(
                nombre="DIRECCION DEL INSTITUTO DE VIVIENDA DE MACUSPANA",
                defaults={"tipo": TipoDependencia.DIRECCION},
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Dependencia creada: {dep_vivienda.nombre}")
                )
            else:
                self.stdout.write(f"Dependencia encontrada: {dep_vivienda.nombre}")

            assets_dir = Path(settings.BASE_DIR) / "data" / "assets"
            programas_data = [
                {
                    "nombre": "Programa de Regularización Predial",
                    "descripcion": "Aprovecha los descuentos y regulariza tu predial. Válido durante enero, febrero y marzo 2026.",
                    "categoria": "Servicios Municipales",
                    "imagen": "programa-regularizacion-predial.png",
                    "dependencia": dep_finanzas,
                    "requisitos": [
                        {
                            "nombre": "Recibos de pago predial 2025",
                            "es_obligatorio": True,
                            "requiere_documento": True,
                        },
                        {
                            "nombre": "Copia INE Vigente",
                            "es_obligatorio": True,
                            "requiere_documento": True,
                        },
                        {
                            "nombre": "CURP Actualizada",
                            "es_obligatorio": True,
                            "requiere_documento": True,
                        },
                    ],
                },
                {
                    "nombre": "Servicios de Atención a las Mujeres",
                    "descripcion": "Servicios gratuitos: asesorías jurídicas, pensión alimenticia, guardia y custodia, divorcio necesario, acompañamiento a fiscalía, asesorías psicológicas, terapia individual, terapia de pareja y terapia familiar.",
                    "categoria": "Servicios Sociales",
                    "imagen": "programa-atencion-mujeres.png",
                    "dependencia": dep_mujeres,
                    "requisitos": [
                        {
                            "nombre": "Identificación Oficial (INE)",
                            "es_obligatorio": True,
                            "requiere_documento": True,
                        },
                    ],
                },
                {
                    "nombre": "Programa Mejorar para Transformar a la Vivienda 2025",
                    "descripcion": "Apoyo para mejora de vivienda. Costos: Rotoplas con bomba $2,580 | Rotoplas sin filtro $2,250. Requisitos: Identificación oficial vigente (INE), realizar pago por medio de transferencia o depósito Santandreu.",
                    "categoria": "Vivienda",
                    "imagen": "programa-mejorar-vivienda.png",
                    "dependencia": dep_vivienda,
                    "requisitos": [
                        {
                            "nombre": "Identificación Oficial Vigente (INE)",
                            "es_obligatorio": True,
                            "requiere_documento": True,
                        },
                        {
                            "nombre": "Comprobante de Pago",
                            "es_obligatorio": True,
                            "requiere_documento": True,
                        },
                    ],
                },
            ]

            for prog_info in programas_data:
                prog, created = ProgramaSocial.objects.get_or_create(
                    nombre=prog_info["nombre"],
                    defaults={
                        "dependencia": prog_info["dependencia"],
                        "descripcion": prog_info["descripcion"],
                        "categoria": prog_info["categoria"],
                        "esta_activo": True,
                        "destacado": True,
                    },
                )

                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f"Programa creado: {prog.nombre}")
                    )
                    # Crear requisitos para el programa recién creado
                    for req_info in prog_info.get("requisitos", []):
                        Requisito.objects.create(
                            programa=prog,
                            nombre=req_info["nombre"],
                            es_obligatorio=req_info["es_obligatorio"],
                            requiere_documento=req_info["requiere_documento"],
                        )
                else:
                    self.stdout.write(f"Programa ya existente: {prog.nombre}")
                    # Actualizar dependencia si es diferente
                    if prog.dependencia != prog_info["dependencia"]:
                        prog.dependencia = prog_info["dependencia"]
                        prog.save()
                        self.stdout.write(
                            self.style.WARNING(
                                f"Programa actualizado con dependencia correcta: {prog.nombre}"
                            )
                        )

                # Agregar imagen si existe y el programa no tiene una
                if prog_info["imagen"]:
                    asset_path = assets_dir / prog_info["imagen"]
                    if asset_path.exists() and not prog.imagen:
                        with asset_path.open("rb") as image_file:
                            prog.imagen.save(
                                prog_info["imagen"], File(image_file), save=True
                            )
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Imagen asociada a programa: {prog.nombre}"
                            )
                        )
                    elif not asset_path.exists():
                        self.stdout.write(
                            self.style.WARNING(
                                f"Imagen no encontrada para {prog.nombre}: {asset_path}"
                            )
                        )

        self.stdout.write(
            self.style.SUCCESS(
                "Proceso de sembrado de programas completado exitosamente."
            )
        )
