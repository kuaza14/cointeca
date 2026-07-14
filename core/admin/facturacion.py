from django.contrib import admin
from core.models import (
    ProyectoFacturacion,
    SeguimientoFacturacion,
)

admin.site.register(ProyectoFacturacion)
admin.site.register(SeguimientoFacturacion)