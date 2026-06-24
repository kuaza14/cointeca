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
    return HttpResponse(
        "Pendiente generar word"
    )
