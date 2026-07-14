from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponse
import os 
from datetime import datetime
from core.models import Empleado, InduccionCapacitacion
from django.conf import settings
from docxtpl import DocxTemplate
from django.http import FileResponse
import re
from core.utils import limpiar_nombre_archivo

@login_required
def inducciones_empleado(request, id):

    empleado = get_object_or_404(
        Empleado,
        id=id
    )

    inducciones = InduccionCapacitacion.objects.filter(
        empleado=empleado
    ).order_by('-id')

    return render(
        request,
        'rrhh/induccion_capacitacion/inducciones_empleado.html',
        {
            'empleado': empleado,
            'inducciones': inducciones
        }
    )

@login_required
def crear_induccion(request, id):

    empleado = get_object_or_404(
        Empleado,
        id=id
    )

    if request.method == 'POST':

        InduccionCapacitacion.objects.create(

            empleado=empleado,

            fecha=request.POST.get(
                'fecha'
            ),

            tema_capacitacion=request.POST.get(
                'tema_capacitacion'
            ) or None,

            facilitador=request.POST.get(
                'facilitador'
            ) or None,

            duracion_horas=request.POST.get(
                'duracion_horas'
            ) or None

        )

        messages.success(
            request,
            'Registro creado correctamente.'
        )

        return redirect(
            'inducciones_empleado',
            id=empleado.id
        )

    return render(
        request,
        'rrhh/induccion_capacitacion/crear_induccion.html',
        {
            'empleado': empleado
        }
    )

@login_required
def editar_induccion(request, id):

    induccion = get_object_or_404(
        InduccionCapacitacion,
        id=id
    )

    if request.method == 'POST':

        induccion.fecha = request.POST.get(
            'fecha'
        )

        induccion.tipo_evento = request.POST.get(
            'tipo_evento'
        )

        induccion.tema_capacitacion = (
            request.POST.get(
                'tema_capacitacion'
            ) or None
        )

        induccion.facilitador = (
            request.POST.get(
                'facilitador'
            ) or None
        )

        induccion.duracion_horas = (
            request.POST.get(
                'duracion_horas'
            ) or None
        )

        induccion.save()

        messages.success(
            request,
            'Inducción actualizada correctamente.'
        )

        return redirect(
            'inducciones_empleado',
            id=induccion.empleado.id
        )

    return render(
        request,
        'rrhh/induccion_capacitacion/editar_induccion.html',
        {
            'induccion': induccion
        }
    )

@login_required
def eliminar_induccion(request, id):

    induccion = get_object_or_404(
        InduccionCapacitacion,
        id=id
    )

    empleado_id = induccion.empleado.id

    if request.method == 'POST':

        induccion.delete()

        messages.success(
            request,
            'Inducción eliminada correctamente.'
        )

    return redirect(
        'inducciones_empleado',
        id=empleado_id
    )

@login_required
def generar_induccion(request, id):

    induccion = get_object_or_404(
        InduccionCapacitacion,
        id=id
    )

    empleado = induccion.empleado

    ruta_plantilla = os.path.join(
        settings.BASE_DIR,
        'plantillas_word',
        'induccion_capacitacion.docx'
    )

    doc = DocxTemplate(
        ruta_plantilla
    )

    contexto = {

        'fecha': induccion.fecha.strftime(
            '%d/%m/%Y'
        ),

        'nombre_completo': empleado.nombre_completo,

        'cedula': empleado.documento,

        'cargo': empleado.cargo,

        'area': empleado.area,

        'fecha_ingreso': empleado.fecha_ingreso.strftime(
            '%d/%m/%Y'
        ),

        'tema_capacitacion': (
            induccion.tema_capacitacion
            or ''
        ),

        'facilitador': (
            induccion.facilitador
            or ''
        ),

        'duracion_horas': (
            induccion.duracion_horas
            or ''
        ),

    }

    doc.render(
        contexto
    )

    nombre_limpio = limpiar_nombre_archivo(
        empleado.nombre_completo
    )

    nombre_archivo = (
        f"Induccion_{nombre_limpio}.docx"
    )

    ruta_salida = os.path.join(
        settings.MEDIA_ROOT,
        nombre_archivo
    )

    doc.save(
        ruta_salida
    )

    return FileResponse(
        open(
            ruta_salida,
            'rb'
        ),
        as_attachment=True,
        filename=nombre_archivo
    )
