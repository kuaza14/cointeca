from django.contrib import admin
from .models import CajaMenor, MovimientoCajaMenor, ActaJuntaDirectiva


admin.site.register(CajaMenor)
admin.site.register(MovimientoCajaMenor)
admin.site.register(ActaJuntaDirectiva)