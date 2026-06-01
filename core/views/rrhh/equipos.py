from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import FileResponse

from docxtpl import DocxTemplate

from datetime import date
import os

from core.models import (
    Empleado,
    AsignacionEquipo,
    InventarioEquipo,
)

@login_required
def asignar_equipo(request, id):

    empleado = Empleado.objects.get(id=id)

    equipos = InventarioEquipo.objects.filter(
        estado='Disponible'
    )

    if request.method == 'POST':

        equipo = InventarioEquipo.objects.get(
            id=request.POST['equipo_inventario']
        )

        AsignacionEquipo.objects.create(
            empleado=empleado,
            equipo_inventario=equipo,
            fecha_entrega=request.POST['fecha_entrega'],
            observaciones=request.POST['observaciones']
        )

        # CAMBIAR ESTADO
        equipo.estado = 'Asignado'
        equipo.save()

        return redirect(f'/rrhh/empleados/{id}/')

    return render(request, 'rrhh/asignar_equipo.html', {
        'empleado': empleado,
        'equipos': equipos
    })
    

@login_required
def eliminar_equipo(request, id):

    equipo = AsignacionEquipo.objects.get(id=id)

    empleado_id = equipo.empleado.id

    equipo.delete()

    return redirect(f'/rrhh/empleados/{empleado_id}/')

@login_required
def editar_equipo(request, id):

    equipo = AsignacionEquipo.objects.get(id=id)

    empleado = equipo.empleado

    if request.method == 'POST':

        existe_serial = AsignacionEquipo.objects.filter(
            serial=request.POST['serial']
        ).exclude(id=id).exists()

        if existe_serial:

            return render(request, 'editar_equipo.html', {
                'empleado': empleado,
                'equipo': equipo,
                'error': '⚠️ Este serial ya está asignado a otro empleado'
            })

        equipo.equipo = request.POST['equipo']
        equipo.referencia = request.POST['referencia']
        equipo.serial = request.POST['serial']
        equipo.fecha_entrega = request.POST['fecha_entrega']
        equipo.observaciones = request.POST['observaciones']

        equipo.save()

        return redirect(f'/rrhh/empleados/{empleado.id}/')

    return render(request, 'editar_equipo.html', {
        'empleado': empleado,
        'equipo': equipo
    })

@login_required
def acta_entrega_equipos(request, id):

    empleado = get_object_or_404(Empleado, id=id)
    equipos = AsignacionEquipo.objects.filter(empleado=empleado)

    ruta_plantilla = os.path.join(
        settings.BASE_DIR,
        "core",
        "templates",
        "rrhh",
        "contratos",
        "acta_entrega.docx"
    )

    doc = DocxTemplate(ruta_plantilla)

    contexto = {
        "empleado": {
            "nombre_completo": empleado.nombre_completo.upper(),
            "documento": empleado.documento,
            "cargo": empleado.cargo.upper(),
        },

        "equipos": equipos,

        "fecha_actual": date.today().strftime("%d/%m/%Y"),
    }

    doc.render(contexto)

    ruta_salida = os.path.join(
        settings.MEDIA_ROOT,
        f"acta_entrega_{empleado.nombre_completo}.docx"
    )

    doc.save(ruta_salida)

    return FileResponse(
        open(ruta_salida, "rb"),
        as_attachment=True,
        filename=f"acta_entrega_{empleado.nombre_completo}.docx"
    )

@login_required
def inventario_equipos(request):

    equipos = InventarioEquipo.objects.all()

    # ACTUALIZAR ESTADO AUTOMÁTICAMENTE
    for e in equipos:

        asignado = AsignacionEquipo.objects.filter(
            equipo_inventario=e
        ).exists()

        if asignado:
            e.estado = 'Asignado'
        else:
            e.estado = 'Disponible'

        e.save()

    return render(request, 'rrhh/inventario_equipos.html', {
        'equipos': equipos
    })

@login_required
def crear_equipo_inventario(request):

    if request.method == 'POST':

        InventarioEquipo.objects.create(

            equipo=request.POST['equipo'],
            referencia=request.POST['referencia'],
            serial=request.POST['serial'],
            fecha_compra=request.POST['fecha_compra'],
            estado=request.POST['estado'],
            observaciones=request.POST['observaciones']

        )

        return redirect('inventario_equipos')

    return render(request, 'rrhh/crear_equipo_inventario.html')

@login_required
def editar_equipo_inventario(request, id):

    equipo = InventarioEquipo.objects.get(id=id)

    if request.method == 'POST':

        equipo.equipo = request.POST['equipo']
        equipo.referencia = request.POST['referencia']
        equipo.serial = request.POST['serial']
        equipo.marca = request.POST['marca']
        equipo.estado = request.POST['estado']
        equipo.fecha_compra = request.POST['fecha_compra']
        equipo.observaciones = request.POST['observaciones']

        equipo.save()

        return redirect('inventario_equipos')

    contexto = {
        'equipo': equipo
    }

    return render(
        request,
        'rrhh/editar_equipo_inventario.html',
        contexto
    )

@login_required
def eliminar_equipo_inventario(request, id):

    equipo = InventarioEquipo.objects.get(id=id)

    equipo.delete()

    return redirect('inventario_equipos')
