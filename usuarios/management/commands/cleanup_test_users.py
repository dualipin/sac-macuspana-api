from django.core.management.base import BaseCommand
from usuarios.models import Usuario

class Command(BaseCommand):
    help = 'Elimina usuarios de prueba creados durante tests o verificaciones (verify_user_*)'

    def handle(self, *args, **options):
        users_to_delete = Usuario.objects.filter(username__startswith='verify_user_')
        count = users_to_delete.count()
        
        if count == 0:
            self.stdout.write(self.style.WARNING("No se encontraron usuarios de prueba 'verify_user_'."))
            return

        confirm = input(f"Se encontraron {count} usuarios de prueba. ¿Desea eliminarlos? (s/n): ")
        if confirm.lower() == 's':
            users_to_delete.delete()
            self.stdout.write(self.style.SUCCESS(f"Se eliminaron {count} usuarios correctamente."))
        else:
            self.stdout.write(self.style.WARNING("Operación cancelada."))
