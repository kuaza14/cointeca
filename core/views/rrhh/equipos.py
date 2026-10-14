from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.conf import settings
from django.http import FileResponse
from django.contrib import messages

from docxtpl import DocxTemplate

from datetime import date
import os

from core.utils import limpiar_nombre_archivo
from core.models import (
    Empleado,
    AsignacionEquipo,
    InventarioEquipo,
)

@login_required
def asignar_equipo(request, id):

    empleado = get_object_or_404(Empleado, id=id)

    equipos = InventarioEquipo.objects.filter(
        estado__iexact='disponible'
)

    if request.method == 'POST':

        equipo_id = request.POST.get('equipo_inventario')
        fecha_entrega = request.POST.get('fecha_entrega')

        if equipo_id and fecha_entrega:
            with transaction.atomic():
                equipo = get_object_or_404(
                    InventarioEquipo.objects.select_for_update(),
                    id=equipo_id
                )

                AsignacionEquipo.objects.create(
                    empleado=empleado,
                    equipo_inventario=equipo,
                    fecha_entrega=fecha_entrega,
                    observaciones=request.POST.get('observaciones', '')
                )

                # CAMBIAR ESTADO
                equipo.estado = 'Asignado'
                equipo.save()

        return redirect(f'/rrhh/empleados/{id}/')

    return render(request, 'rrhh/equipos/asignar_equipo.html', {
        'empleado': empleado,
        'equipos': equipos
    })
    

@login_required
def eliminar_equipo(request, id):
    equipo = get_object_or_404(AsignacionEquipo, id=id)
    empleado_id = equipo.empleado.id

    if request.method == 'POST':
        if equipo.equipo_inventario:
            equipo.equipo_inventario.estado = 'Disponible'
            equipo.equipo_inventario.save()

        equipo.delete()
        messages.success(request, "Equipo / Herramienta devuelto al inventario de bodega correctamente.")

    return redirect(f'/rrhh/empleados/{empleado_id}/')

@login_required
def editar_equipo(request, id):

    equipo = get_object_or_404(AsignacionEquipo, id=id)

    empleado = equipo.empleado

    if request.method == 'POST':

        # serial/referencia/equipo viven en InventarioEquipo (FK equipo_inventario)
        inventario = equipo.equipo_inventario

        if inventario:
            existe_serial = InventarioEquipo.objects.filter(
                serial=request.POST['serial']
).exclude(id=inventario.id).exists()

            if existe_serial:

                return render(request, 'rrhh/equipos/editar_equipo.html', {
                    'empleado': empleado,
                    'equipo': equipo,
                    'error': ' Este serial ya pertenece a otro equipo del inventario'
                })

            inventario.equipo = request.POST['equipo']
            inventario.referencia = request.POST['referencia']
            inventario.serial = request.POST['serial']
            inventario.marca = request.POST.get('marca', '')
            inventario.save()

        equipo.fecha_entrega = request.POST['fecha_entrega']
        equipo.observaciones = request.POST.get('observaciones', '')

        equipo.save()

        return redirect(f'/rrhh/empleados/{empleado.id}/')

    return render(request, 'rrhh/equipos/editar_equipo.html', {
        'empleado': empleado,
        'equipo': equipo
    })

@login_required
def acta_entrega_equipos(request, id):

    empleado = get_object_or_404(Empleado, id=id)
    equipos = AsignacionEquipo.objects.filter(empleado=empleado)

    if not equipos.exists():
        messages.warning(
            request,
            "Primero debe asignar un equipo al empleado."
)
        return redirect(f"/rrhh/empleados/{empleado.id}/")

    ruta_plantilla = os.path.join(
        settings.BASE_DIR,
        "plantillas_word",
        "asignacion_equipos.docx"
)    

    doc = DocxTemplate(ruta_plantilla)

    contexto = {
        "empleado": {
            "nombre_completo": empleado.nombre_completo.upper(),
            "documento": empleado.documento,
            "cargo": empleado.cargo.upper(),
        },

        "e": equipos.first(),

        "fecha_actual": date.today().strftime("%d/%m/%Y"),
    }

    doc.render(contexto)

    ruta_salida = os.path.join(
        settings.MEDIA_ROOT,
        f"acta_entrega_{limpiar_nombre_archivo(empleado.nombre_completo)}_{empleado.id}.docx"
)

    doc.save(ruta_salida)

    return FileResponse(
        open(ruta_salida, "rb"),
        as_attachment=True,
        filename=f"acta_entrega_{limpiar_nombre_archivo(empleado.nombre_completo)}_{empleado.id}.docx"
)

@login_required
def inventario_equipos(request):

    equipos = InventarioEquipo.objects.all()

    # ACTUALIZAR ESTADO AUTOMÁTICAMENTE
    # Solo alterna Disponible/Asignado: conserva Dañado, Baja, Mantenimiento
    for e in equipos:

        asignado = AsignacionEquipo.objects.filter(
            equipo_inventario=e
).exists()

        if asignado and e.estado.lower()!= 'asignado':
            e.estado = 'Asignado'
            e.save(update_fields=['estado'])
        elif not asignado and e.estado.lower() == 'asignado':
            e.estado = 'Disponible'
            e.save(update_fields=['estado'])

    return render(request, 'rrhh/equipos/inventario_equipos.html', {
        'equipos': equipos
    })

@login_required
def crear_equipo_inventario(request):

    if request.method == 'POST':

        equipo_nombre = request.POST.get('equipo', '').strip()
        serial = request.POST.get('serial', '').strip()
        fecha_compra = request.POST.get('fecha_compra')

        if equipo_nombre and serial and fecha_compra:

            InventarioEquipo.objects.create(

                equipo=equipo_nombre,
                referencia=request.POST.get('referencia', '').strip(),
                serial=serial,
                marca=request.POST.get('marca', ''),
                fecha_compra=fecha_compra,
                estado=request.POST.get('estado') or 'Disponible',
                observaciones=request.POST.get('observaciones', '')

            )

        return redirect('inventario_equipos')

    return render(request, 'rrhh/equipos/crear_equipo_inventario.html')

@login_required
def editar_equipo_inventario(request, id):

    equipo = get_object_or_404(InventarioEquipo, id=id)

    if request.method == 'POST':

        equipo.equipo = request.POST.get('equipo') or equipo.equipo
        equipo.referencia = request.POST.get('referencia', '')
        equipo.serial = request.POST.get('serial') or equipo.serial
        equipo.marca = request.POST.get('marca', '')
        equipo.estado = request.POST.get('estado') or equipo.estado
        equipo.fecha_compra = request.POST.get('fecha_compra') or equipo.fecha_compra
        equipo.observaciones = request.POST.get('observaciones', '')

        equipo.save()

        return redirect('inventario_equipos')

    contexto = {
        'equipo': equipo
    }

    return render(
        request,
        'rrhh/equipos/editar_equipo_inventario.html',
        contexto
)

@login_required
def eliminar_equipo_inventario(request, id):

    equipo = get_object_or_404(InventarioEquipo, id=id)

    if request.method == 'POST':
        equipo.delete()
        messages.success(request, 'Equipo eliminado del inventario correctamente.')

    return redirect('inventario_equipos')
