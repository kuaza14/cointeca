from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from core.models import (
    ProyectoFacturacion,
    SeguimientoFacturacion,
)


# Vistas de Facturación
@login_required
def facturacion(request):
    proyectos = ProyectoFacturacion.objects.filter(activo=True)
    seguimientos = SeguimientoFacturacion.objects.all().order_by('anio', 'mes')
    return render(request, 'gerencia/facturacion/facturacion.html', {
        'proyectos': proyectos,
        'seguimientos': seguimientos
    })

@login_required
def crear_proyecto(request):
    if request.method == 'POST':
        ProyectoFacturacion.objects.create(
            nombre=request.POST['nombre']
        )
        return redirect('/facturacion/')
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
        return redirect('/facturacion/')
    return render(request, 'gerencia/facturacion/registrar_facturacion.html', {'proyectos': proyectos})

@login_required
def eliminar_facturacion(request, id):
    seguimiento = get_object_or_404(SeguimientoFacturacion, id=id)
    seguimiento.delete()
    return redirect('/facturacion/')

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
        return redirect('/facturacion/')
    return render(request, 'gerencia/facturacion/editar_facturacion.html', {
        'seguimiento': seguimiento,
        'proyectos': proyectos
    })
