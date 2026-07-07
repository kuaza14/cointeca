from django.contrib import admin

from core.models import (
    InventarioEquipo,
    AsignacionEquipo,
    ActaEntregaEquipo,
)

admin.site.register(InventarioEquipo)
admin.site.register(AsignacionEquipo)
admin.site.register(ActaEntregaEquipo)