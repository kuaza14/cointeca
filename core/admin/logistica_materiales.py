from django.contrib import admin
from core.models import (
    Material,
    EntradaMaterialProyecto,
    DetalleEntradaMaterial,
    ConsumoMaterialProyecto,
    DetalleConsumoMaterial,
)


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ["item", "descripcion", "unidad"]
    search_fields = ["item", "descripcion"]
    ordering = ["item"]


class DetalleEntradaMaterialInline(admin.TabularInline):
    model = DetalleEntradaMaterial
    extra = 1
    autocomplete_fields = ["material"]


@admin.register(EntradaMaterialProyecto)
class EntradaMaterialProyectoAdmin(admin.ModelAdmin):
    list_display = ["proyecto", "fecha", "numero_remision", "proveedor", "recibido_por", "fecha_creacion"]
    list_filter = ["fecha", "proyecto"]
    search_fields = ["numero_remision", "proveedor", "recibido_por", "proyecto__numero_emcali"]
    inlines = [DetalleEntradaMaterialInline]


class DetalleConsumoMaterialInline(admin.TabularInline):
    model = DetalleConsumoMaterial
    extra = 1
    autocomplete_fields = ["material"]


@admin.register(ConsumoMaterialProyecto)
class ConsumoMaterialProyectoAdmin(admin.ModelAdmin):
    list_display = ["proyecto", "fecha_reporte", "supervisor", "numero_planilla", "fecha_creacion"]
    list_filter = ["fecha_reporte", "proyecto"]
    search_fields = ["supervisor", "numero_planilla", "proyecto__numero_emcali"]
    inlines = [DetalleConsumoMaterialInline]
