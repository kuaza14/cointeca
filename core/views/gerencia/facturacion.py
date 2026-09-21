from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum

from core.models import (
    ProyectoFacturacion,
    SeguimientoFacturacion,
)


# Vistas de Facturación dentro de Gerencia
@login_required
def facturacion(request):
    proyectos = ProyectoFacturacion.objects.filter(activo=True)
    seguimientos = SeguimientoFacturacion.objects.select_related('proyecto').all().order_by('-anio', 'mes')

    total_meta = sum([s.meta_facturacion for s in seguimientos]) if seguimientos else 0
    total_real = sum([s.facturacion_real for s in seguimientos]) if seguimientos else 0
    porcentaje_global = round((total_real / total_meta * 100), 1) if total_meta > 0 else 0

    return render(request, 'gerencia/facturacion/facturacion.html', {
        'proyectos': proyectos,
        'seguimientos': seguimientos,
        'total_meta': total_meta,
        'total_real': total_real,
        'porcentaje_global': porcentaje_global,
    })

@login_required
def crear_proyecto_facturacion(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        if nombre:
            ProyectoFacturacion.objects.create(nombre=nombre)
        return redirect('facturacion')
    return render(request, 'gerencia/facturacion/crear_proyecto.html')

@login_required
def registrar_facturacion(request):
    proyectos = ProyectoFacturacion.objects.filter(activo=True)
    if request.method == 'POST':
        SeguimientoFacturacion.objects.create(
            mes=request.POST['mes'],
            anio=request.POST['anio'],
            meta_facturacion=request.POST['meta_facturacion'].replace(',', '').replace('.', ''),
            facturacion_real=request.POST['facturacion_real'].replace(',', '').replace('.', ''),
            proyecto_id=request.POST['proyecto']
        )
        return redirect('facturacion')
    return render(request, 'gerencia/facturacion/registrar_facturacion.html', {'proyectos': proyectos})

@login_required
def eliminar_facturacion(request, id):
    seguimiento = get_object_or_404(SeguimientoFacturacion, id=id)
    seguimiento.delete()
    return redirect('facturacion')

@login_required
def editar_facturacion(request, id):
    seguimiento = get_object_or_404(SeguimientoFacturacion, id=id)
    proyectos = ProyectoFacturacion.objects.filter(activo=True)
    if request.method == 'POST':
        seguimiento.mes = request.POST['mes']
        seguimiento.anio = request.POST['anio']
        seguimiento.meta_facturacion = request.POST['meta_facturacion'].replace(',', '').replace('.', '')
        seguimiento.facturacion_real = request.POST['facturacion_real'].replace(',', '').replace('.', '')
        seguimiento.proyecto_id = request.POST['proyecto']
        seguimiento.save()
        return redirect('facturacion')
    return render(request, 'gerencia/facturacion/editar_facturacion.html', {
        'seguimiento': seguimiento,
        'proyectos': proyectos
    })

