from django.contrib import admin

from core.models import (
    Descargo,
    CitacionDescargo,
)

admin.site.register(Descargo)
admin.site.register(CitacionDescargo)