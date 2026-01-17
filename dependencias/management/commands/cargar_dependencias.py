import pandas as pd
import re
from django.core.management.base import BaseCommand
from django.db import transaction, connection
from django.contrib.auth.hashers import make_password
from dependencias.models import Dependencia, Funcionario
from usuarios.models import Usuario
from core.choices import Roles


class Command(BaseCommand):
    help = 'Carga jerárquica de Dependencias, Usuarios y Funcionarios'

    def add_arguments(self, parser):
        parser.add_argument('ruta', type=str)

    def correo_temporal(self, nombre, apellido):
        nombre = str(nombre) if nombre else ""
        apellido = str(apellido) if apellido else ""
        nombre_limpio = re.sub(r'[^a-zA-Z\s]', '', nombre).lower().replace(' ', '')
        apellido_limpio = re.sub(r'[^a-zA-Z]', '', apellido).lower()
        return f"{nombre_limpio}.{apellido_limpio}@macuspana.gob.mx"

    def handle(self, *args, **options):
        df = pd.read_csv(options['ruta'], dtype=str).fillna('')
        batch_size = 900 if connection.vendor == 'sqlite' else 5000

        with transaction.atomic():
            self.stdout.write("Limpiando datos previos...")
            Funcionario.objects.all().delete()
            Usuario.objects.exclude(is_superuser=True).delete()
            Dependencia.objects.all().delete()

            # PASO 1: Crear Dependencias
            dep_map = {}
            for _, row in df.iterrows():
                dep = Dependencia.objects.create(
                    nombre=row['nombre'].upper(),
                    siglas=row['abreviatura'].upper() if row['abreviatura'] else None,
                    tipo=row['tipo'].lower()
                )
                dep_map[row['id']] = dep

            # PASO 2: Crear Usuarios en bloque (bulk_create)
            # Pre-generamos datos para evitar múltiples hits a BD
            self.stdout.write("Generando cuentas de usuario...")
            usuarios_objs = []
            for _, row in df.iterrows():
                correo = self.correo_temporal(row['nombre_representante'], row['apellido_paterno'])

                is_admin = row['tipo_usuario'] == 'admin'

                usuarios_objs.append(Usuario(
                    username=correo,
                    rol=Roles.ADMINISTRADOR if is_admin else Roles.FUNCIONARIO,
                    is_superuser=is_admin,
                    is_staff=is_admin,
                    password=make_password("Temporal123")  # Password por defecto
                ))

            Usuario.objects.bulk_create(usuarios_objs, batch_size=batch_size)

            # Mapeamos usuarios recién creados {username: objeto_usuario}
            user_map = {u.username: u for u in Usuario.objects.all()}

            # PASO 3: Crear Funcionarios vinculados a Usuario y Dependencia
            self.stdout.write("Vinculando funcionarios...")
            funcionarios_a_crear = []
            for _, row in df.iterrows():
                correo = self.correo_temporal(row['nombre_representante'], row['apellido_paterno'])
                nom_comp = f"{row['nombre_representante']} {row['apellido_paterno']} {row['apellido_materno']}".strip().upper()

                funcionarios_a_crear.append(Funcionario(
                    nombre_completo=nom_comp,
                    correo=correo,
                    telefono=row['telefono'],
                    cargo="TITULAR",
                    sexo=row['sexo'].upper(),
                    dependencia=dep_map[row['id']],
                    usuario=user_map[correo]  # Vínculo OneToOne
                ))

            Funcionario.objects.bulk_create(funcionarios_a_crear, batch_size=batch_size)

            # PASO 4: Asignar Representante a la Dependencia (Cierre de círculo)
            self.stdout.write("Asignando titulares a dependencias...")
            func_map = {f.correo: f for f in Funcionario.objects.all()}
            for csv_id, dep_obj in dep_map.items():
                # Obtenemos el correo de esa fila del DF original para buscar al funcionario
                fila = df[df['id'] == csv_id].iloc[0]
                correo = self.correo_temporal(fila['nombre_representante'], fila['apellido_paterno'])
                dep_obj.representante = func_map[correo]
                dep_obj.save()

        self.stdout.write(self.style.SUCCESS('✅ Proceso completado exitosamente.'))
