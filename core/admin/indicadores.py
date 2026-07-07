from django.contrib import admin

from core.models import (
    IndicadorEstrategico,
    SeguimientoIndicador,
)

admin.site.register(IndicadorEstrategico)
admin.site.register(SeguimientoIndicador)