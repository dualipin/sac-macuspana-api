from servicios.models import TramiteCatalogo

tramite = TramiteCatalogo.objects.filter(id=1).first()
if tramite:
    print(f"Trámite ID 1: {tramite.nombre}")
    print(f"Esta activo: {tramite.esta_activo}")
    print(f"Destacado: {tramite.destacado}")
else:
    print("Trámite con ID 1 no encontrado")

print("\nTodos los trámites:")
for t in TramiteCatalogo.objects.all():
    print(f"  ID {t.id}: {t.nombre} - Activo: {t.esta_activo}")
