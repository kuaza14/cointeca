from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponse
import os 
from datetime import datetime
from core.models import Empleado, CompromisoPagoDano
from django.conf import settings
from docxtpl import DocxTemplate
from django.http import FileResponse
import re
from core.utils import limpiar_nombre_archivo, formatear_pesos

@login_required
def compromisos_empleado(request, id):

    empleado = get_object_or_404(
        Empleado,
        id=id
    )

    compromisos = CompromisoPagoDano.objects.filter(
        empleado=empleado
    ).order_by('-id')

    return render(
        request,
        'rrhh/compromiso_dano/compromisos_empleado.html',
        {
            'empleado': empleado,
            'compromisos': compromisos
        }
    )

@login_required
def crear_compromiso(request, id):

    empleado = get_object_or_404(
        Empleado,
        id=id
    )

    if request.method == 'POST':

        CompromisoPagoDano.objects.create(

            empleado=empleado,

            numero_acta=request.POST.get(
                'numero_acta'
            ),

            valor_descuento=request.POST.get(
                'valor_descuento'
            ),

            descripcion_dano=request.POST.get(
                'descripcion_dano'
            ),

            fecha_evento=request.POST.get(
                'fecha_evento'
            )

        )

        messages.success(
            request,
            'Compromiso creado correctamente.'
        )

        return redirect(
            'compromisos_empleado',
            id=empleado.id
        )

    return render(
        request,
        'rrhh/compromiso_dano/crear_compromiso.html',
        {
            'empleado': empleado
        }
    )

@login_required
def editar_compromiso(request, id):

    compromiso = get_object_or_404(
        CompromisoPagoDano,
        id=id
    )

    if request.method == 'POST':

        compromiso.numero_acta = request.POST.get(
            'numero_acta'
        )

        compromiso.valor_descuento = request.POST.get(
            'valor_descuento'
        )

        compromiso.descripcion_dano = request.POST.get(
            'descripcion_dano'
        )

        compromiso.fecha_evento = request.POST.get(
            'fecha_evento'
        )

        compromiso.save()

        messages.success(
            request,
            'Compromiso actualizado correctamente.'
        )

        return redirect(
            'compromisos_empleado',
            id=compromiso.empleado.id
        )

    return render(
        request,
        'rrhh/compromiso_dano/editar_compromiso.html',
        {
            'compromiso': compromiso
        }
    )

@login_required
def eliminar_compromiso(request, id):

    compromiso = get_object_or_404(
        CompromisoPagoDano,
        id=id
    )

    empleado_id = compromiso.empleado.id

    if request.method == 'POST':

        compromiso.delete()

        messages.success(
            request,
            'Compromiso eliminado correctamente.'
        )

    return redirect(
        'compromisos_empleado',
        id=empleado_id
    )

@login_required
def generar_compromiso(request, id):

    compromiso = get_object_or_404(
        CompromisoPagoDano,
        id=id
    )

    empleado = compromiso.empleado

    ruta_plantilla = os.path.join(
        settings.BASE_DIR,
        'plantillas_word',
        'compromiso_pago_dano.docx'
    )

    doc = DocxTemplate(
        ruta_plantilla
    )

    fecha_actual = datetime.now()

    meses = {
        1: 'enero',
        2: 'febrero',
        3: 'marzo',
        4: 'abril',
        5: 'mayo',
        6: 'junio',
        7: 'julio',
        8: 'agosto',
        9: 'septiembre',
        10: 'octubre',
        11: 'noviembre',
        12: 'diciembre'
    }

    contexto = {

        'nombre_completo': empleado.nombre_completo,

        'documento': empleado.documento,

        'cargo': empleado.cargo,

        'valor_descuento': formatear_pesos(
            compromiso.valor_descuento
        ),

        'numero_acta': compromiso.numero_acta,

        'descripcion_dano': compromiso.descripcion_dano,

        'fecha_evento': compromiso.fecha_evento.strftime(
            '%d/%m/%Y'
        ),

        'empresa': 'COINTECA SAS',

        'dia_actual': fecha_actual.day,

        'mes_actual': meses[
            fecha_actual.month
        ],

        'anio_actual': fecha_actual.year

    }

    doc.render(
        contexto
    )

    nombre_archivo = (
        f"Compromiso_Dano_{empleado.documento}.docx"
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