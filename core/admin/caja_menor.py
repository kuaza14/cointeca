from django.contrib import admin

from core.models import (
    CajaMenor,
    MovimientoCajaMenor,
)

admin.site.register(CajaMenor)
admin.site.register(MovimientoCajaMenor)