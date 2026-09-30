from pathlib import Path
from django.core.management import call_command
from django.core.management.base import BaseCommand
from core.models import Material, ItemManoObra, Empleado


class Command(BaseCommand):
    help = 'Carga el catálogo inicial de materiales, mano de obra y empleados si la base está vacía'

    def handle(self, *args, **options):
        fixture_path = Path(__file__).resolve().parent.parent.parent.parent / 'datos_produccion_limpios.json'
        if not fixture_path.exists():
            self.stdout.write(self.style.WARNING("Archivo datos_produccion_limpios.json no encontrado."))
            return

        # Solo carga si la base de datos no tiene estos catálogos
        if Material.objects.count() == 0 and ItemManoObra.objects.count() == 0 and Empleado.objects.count() == 0:
            self.stdout.write("Cargando catálogo limpio de materiales, mano de obra y empleados en producción...")
            call_command('loaddata', str(fixture_path))
            self.stdout.write(
                self.style.SUCCESS(
                    f"¡Carga exitosa! {Material.objects.count()} materiales, "
                    f"{ItemManoObra.objects.count()} ítems de mano de obra y "
                    f"{Empleado.objects.count()} empleados registrados."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("La base de datos ya cuenta con registros. Omitiendo carga inicial para preservar datos.")
            )
