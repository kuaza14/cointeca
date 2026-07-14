from django.contrib import admin

from core.models import (
    Empleado,
    SaludEmpleado,
    DotacionEmpleado,
)

admin.site.register(Empleado)
admin.site.register(SaludEmpleado)
admin.site.register(DotacionEmpleado)