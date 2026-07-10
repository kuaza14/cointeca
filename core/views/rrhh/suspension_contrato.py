from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse

from core.models import Empleado, SuspensionContrato

import os
import tempfile

from datetime import date
from django.conf import settings
from docxtpl import DocxTemplate


@login_required
def suspensiones_empleado(request, id):

    empleado = get_object_or_404(
        Empleado,
        id=id
    )

    suspensiones = SuspensionContrato.objects.filter(
        empleado=empleado
    ).order_by('-fecha_inicio')

    return render(
        request,
        'rrhh/suspensiones/suspensiones_empleado.html',
        {
            'empleado': empleado,
            'suspensiones': suspensiones
        }
    )


@login_required
def crear_suspension(request, id):

    empleado = get_object_or_404(
        Empleado,
        id=id
    )

    if request.method == 'POST':

        SuspensionContrato.objects.create(

            empleado=empleado,

            fecha_inicio=request.POST['fecha_inicio'],

            fecha_fin=request.POST['fecha_fin'],

            motivo=request.POST.get(
                'motivo',
                ''
            ),
        )

        messages.success(
            request,
            '✅ Suspensión registrada correctamente.'
        )

        return redirect(
            f'/rrhh/empleados/{id}/suspensiones/'
        )

    return render(
        request,
        'rrhh/suspensiones/crear_suspension.html',
        {
            'empleado': empleado
        }
    )


@login_required
def editar_suspension(request, id):

    suspension = get_object_or_404(
        SuspensionContrato,
        id=id
    )

    if request.method == 'POST':

        suspension.fecha_inicio = request.POST['fecha_inicio']

        suspension.fecha_fin = request.POST['fecha_fin']

        suspension.save()

        messages.success(
            request,
            '✅ Suspensión actualizada correctamente.'
        )

        return redirect(
            f'/rrhh/empleados/{suspension.empleado.id}/suspensiones/'
        )

    return render(
        request,
        'rrhh/suspensiones/editar_suspension.html',
        {
            'suspension': suspension,
            'empleado': suspension.empleado,
        }
    )


@login_required
def eliminar_suspension(request, id):

    suspension = get_object_or_404(
        SuspensionContrato,
        id=id
    )

    empleado_id = suspension.empleado.id

    suspension.delete()

    messages.success(
        request,
        '✅ Suspensión eliminada correctamente.'
    )

    return redirect(
        f'/rrhh/empleados/{empleado_id}/suspensiones/'
    )


@login_required
def generar_suspension(request, id):

    suspension = get_object_or_404(
        SuspensionContrato,
        id=id
    )

    empleado = suspension.empleado

    gerente = Empleado.objects.filter(
        cargo__iexact="gerente general"
    ).first()

    representante_legal = (
        gerente.nombre_completo if gerente else ""
    )

    cc_representante = (
        gerente.documento if gerente else ""
    )

    ruta_plantilla = os.path.join(
        settings.BASE_DIR,
        "plantillas_word",
        "suspension_contrato.docx"
    )

    doc = DocxTemplate(ruta_plantilla)

    hoy = date.today()

    meses = {
        1: "enero",
        2: "febrero",
        3: "marzo",
        4: "abril",
        5: "mayo",
        6: "junio",
        7: "julio",
        8: "agosto",
        9: "septiembre",
        10: "octubre",
        11: "noviembre",
        12: "diciembre",
    }

    contexto = {

        "empleado": empleado,

        "representante_legal": representante_legal,

        "cc_representante": cc_representante,

        "dia_actual": hoy.day,

        "mes_actual": meses[hoy.month],

        "anio_actual": hoy.year,

        "fecha_inicio_suspension":
            suspension.fecha_inicio.strftime("%d/%m/%Y"),

        "fecha_fin_suspension":
            suspension.fecha_fin.strftime("%d/%m/%Y"),

    }

    doc.render(contexto)

    archivo_salida = os.path.join(
        tempfile.gettempdir(),
        f"Suspension_Contrato_{empleado.documento}.docx"
    )

    doc.save(archivo_salida)

    return FileResponse(
        open(archivo_salida, "rb"),
        as_attachment=True,
        filename=f"Suspension_Contrato_{empleado.documento}.docx"
    )