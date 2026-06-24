from datetime import datetime
import os
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from docxtpl import DocxTemplate
from core.models import (
    Empleado, 
    Descargo,
    CitacionDescargo
)



@login_required
def empleado_descargo(request, id):

    empleado = get_object_or_404(
        Empleado,
        id=id
    )

    descargo = Descargo.objects.filter(
        empleado=empleado
    ).order_by(
        '-id'
    ).first()

    if not descargo:

        return HttpResponse(
            "Este empleado no tiene descargos registrados."
        )

    ruta_plantilla = os.path.join(
        settings.BASE_DIR,
        'plantillas_word',
        'diligencia_descargos.docx'
    )

    doc = DocxTemplate(
        ruta_plantilla
    )

    contexto = {

        'dia_actual':
            datetime.now().day,

        'mes_actual':
            datetime.now().strftime('%B'),

        'anio_actual':
            datetime.now().year,

        'empleado':
            empleado,

        'representante_rrhh':
            descargo.representante_rrhh,

        'testigo':
            descargo.testigo,

        'fecha_hechos':
            descargo.fecha_hechos.strftime(
                '%d/%m/%Y'
            ),

        'descripcion_falta':
            descargo.descripcion_falta,

        'hora_inicio':
            descargo.hora_inicio.strftime(
                '%H:%M'
            )

    }

    doc.render(
        contexto
    )

    ruta_salida = os.path.join(
        settings.MEDIA_ROOT,
        f'descargo_{empleado.id}_{descargo.id}.docx'
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
        filename=f'Descargo_{empleado.nombre_completo}.docx'
    )

@login_required
def crear_descargo(request, id):

    empleado = get_object_or_404(Empleado, id=id)

    # 👇 TODOS los descargos del empleado
    descargos = Descargo.objects.filter(
        empleado=empleado
    ).order_by('-fecha_registro')

    if request.method == 'POST':
        testigo = request.POST.get('testigo')
        fecha_hechos = request.POST.get('fecha_hechos')
        hora_inicio = request.POST.get('hora_inicio')
        descripcion_falta = request.POST.get('descripcion_falta')

        Descargo.objects.create(
            empleado=empleado,
            testigo=testigo,
            fecha_hechos=fecha_hechos,
            hora_inicio=hora_inicio,
            descripcion_falta=descripcion_falta
        )

        return redirect('crear_descargo', id=empleado.id)

    return render(request, 'rrhh/crear_descargo.html', {
        'empleado': empleado,
        'descargos': descargos
    })

@login_required
def descargos_empleado(request, id):

    empleado = get_object_or_404(
        Empleado,
        id=id
    )

    descargos = Descargo.objects.filter(
        empleado=empleado
    ).order_by('-id')

    citaciones = CitacionDescargo.objects.filter(
        empleado=empleado
    ).order_by('-id')

    return render(
        request,
        'rrhh/descargos_empleado.html',
        {
            'empleado': empleado,
            'descargos': descargos,
            'citaciones': citaciones
        }
    )

@login_required
def crear_citacion_descargo(request, id):

    empleado = get_object_or_404(
        Empleado,
        id=id
    )

    if request.method == 'POST':

        CitacionDescargo.objects.create(

            empleado=empleado,

            fecha_diligencia=request.POST.get(
                'fecha_diligencia'
            ),

            hora_diligencia=request.POST.get(
                'hora_diligencia'
            ),

            lugar_diligencia=request.POST.get(
                'lugar_diligencia'
            ),

            descripcion_hechos=request.POST.get(
                'descripcion_hechos'
            ),

            clausula_contrato=request.POST.get(
                'clausula_contrato'
            ),

            articulo_reglamento=request.POST.get(
                'articulo_reglamento'
            ),

            norma_cst=request.POST.get(
                'norma_cst'
            )

        )

        messages.success(
            request,
            'La citación fue registrada correctamente.'
        )

        return redirect(
            'descargos_empleado',
            id=empleado.id
        )

    return render(
        request,
        'rrhh/crear_citacion_descargo.html',
        {
            'empleado': empleado
        }
    )

@login_required
def generar_citacion_descargo(request, id):

    citacion = get_object_or_404(
        CitacionDescargo,
        id=id
    )

    empleado = citacion.empleado

    ruta_plantilla = os.path.join(
        settings.BASE_DIR,
        'plantillas_word',
        'citacion_descargos.docx'
    )

    doc = DocxTemplate(ruta_plantilla)

    contexto = {

        'dia_actual': datetime.now().day,
        'mes_actual': datetime.now().strftime('%B'),
        'anio_actual': datetime.now().year,

        'empleado': empleado,

        'fecha_diligencia':
        citacion.fecha_diligencia.strftime('%d/%m/%Y'),

        'hora_diligencia':
        citacion.hora_diligencia.strftime('%H:%M'),

        'lugar_diligencia':
        citacion.lugar_diligencia,

        'descripcion_hechos':
        citacion.descripcion_hechos,

        'clausula_contrato':
        citacion.clausula_contrato,

        'articulo_reglamento':
        citacion.articulo_reglamento,

        'norma_cst':
        citacion.norma_cst
    }

    doc.render(contexto)

    ruta_salida = os.path.join(
        settings.MEDIA_ROOT,
        f'citacion_descargo_{citacion.id}.docx'
    )

    doc.save(ruta_salida)

    return FileResponse(
        open(ruta_salida, 'rb'),
        as_attachment=True,
        filename=f'Citacion_Descargo_{empleado.nombre_completo}.docx'
    )


@login_required
def editar_descargo(request, id):

    descargo = get_object_or_404(
        Descargo,
        id=id
    )

    if request.method == 'POST':

        descargo.testigo = request.POST.get(
            'testigo'
        )

        descargo.fecha_hechos = request.POST.get(
            'fecha_hechos'
        )

        descargo.hora_inicio = request.POST.get(
            'hora_inicio'
        )

        descargo.hora_cierre = request.POST.get(
            'hora_cierre'
        )

        descargo.descripcion_falta = request.POST.get(
            'descripcion_falta'
        )

        descargo.observaciones_finales = request.POST.get(
            'observaciones_finales'
        )

        descargo.save()

        messages.success(
            request,
            'El descargo fue actualizado correctamente.'
        )

        return redirect(
            'descargos_empleado',
            id=descargo.empleado.id
        )

    return render(
        request,
        'rrhh/editar_descargo.html',
        {
            'descargo': descargo
        }
    )


@login_required
def eliminar_descargo(request, id):

    descargo = get_object_or_404(
        Descargo,
        id=id
    )

    empleado_id = descargo.empleado.id

    descargo.delete()

    messages.success(
        request,
        'El descargo fue eliminado correctamente.'
    )

    return redirect(
        'descargos_empleado',
        id=empleado_id
    )

@login_required
def editar_citacion_descargo(request, id):

    citacion = get_object_or_404(
        CitacionDescargo,
        id=id
    )

    if request.method == 'POST':

        citacion.fecha_diligencia = request.POST.get(
            'fecha_diligencia'
        )

        citacion.hora_diligencia = request.POST.get(
            'hora_diligencia'
        )

        citacion.lugar_diligencia = request.POST.get(
            'lugar_diligencia'
        )

        citacion.descripcion_hechos = request.POST.get(
            'descripcion_hechos'
        )

        citacion.clausula_contrato = request.POST.get(
            'clausula_contrato'
        )

        citacion.articulo_reglamento = request.POST.get(
            'articulo_reglamento'
        )

        citacion.norma_cst = request.POST.get(
            'norma_cst'
        )

        citacion.save()

        messages.success(
            request,
            'La citación fue actualizada correctamente.'
        )

        return redirect(
            'descargos_empleado',
            id=citacion.empleado.id
        )

    return render(
        request,
        'rrhh/editar_citacion_descargo.html',
        {
            'citacion': citacion
        }
    )


@login_required
def eliminar_citacion_descargo(request, id):

    citacion = get_object_or_404(
        CitacionDescargo,
        id=id
    )

    empleado_id = citacion.empleado.id

    citacion.delete()

    messages.success(
        request,
        'La citación fue eliminada correctamente.'
    )

    return redirect(
        'descargos_empleado',
        id=empleado_id
    )