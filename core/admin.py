from django.contrib import admin
from .models import CajaMenor, MovimientoCajaMenor, ActaJuntaDirectiva, Empleado, SaludEmpleado, DotacionEmpleado, InventarioEquipo


admin.site.register(CajaMenor)
admin.site.register(MovimientoCajaMenor)
admin.site.register(ActaJuntaDirectiva)
admin.site.register(Empleado)
admin.site.register(SaludEmpleado)
admin.site.register(DotacionEmpleado)
admin.site.register(InventarioEquipo)