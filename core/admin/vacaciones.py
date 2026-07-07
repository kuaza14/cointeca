from django.contrib import admin

from core.models import (
    SolicitudVacaciones,
    Vacacion,
)

admin.site.register(SolicitudVacaciones)
admin.site.register(Vacacion)