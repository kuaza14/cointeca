from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.shortcuts import redirect
import os 
from datetime import datetime
from core.models import Empleado, RetiroCesantias
from django.conf import settings
from docxtpl import DocxTemplate
from django.http import FileResponse
import re
from num2words import num2words
from core.utils import formatear_pesos

def limpiar_nombre_archivo(nombre):
    return re.sub(r'[\\/*?:"<>|\t\n]', '', nombre).strip().replace(" ", "_")


@login_required
def retiros_cesantias_empleado(request, id):

    empleado = get_object_or_404(
        Empleado,
        id=id
    )

    retiros = RetiroCesantias.objects.filter(
        empleado=empleado
    ).order_by('-id')

    return render(
        request,
        'rrhh/cesantias/retiros_cesantias_empleado.html',
        {
            'empleado': empleado,
            'retiros': retiros
        }
    )

@login_required
def crear_retiro_cesantias(request, id):

    empleado = get_object_or_404(
        Empleado,
        id=id
    )

    if request.method == 'POST':

        RetiroCesantias.objects.create(

            empleado=empleado,

            tipo_retiro=request.POST.get(
                'tipo_retiro'
            ),

            fondo_cesantias=request.POST.get(
                'fondo_cesantias'
            ),

            fecha_solicitud=request.POST.get(
                'fecha_solicitud'
            ),

            valor_retiro=request.POST.get(
                'valor_retiro'
            ),

            direccion_vivienda=request.POST.get(
                'direccion_vivienda'
            ) or None,

            descripcion_vivienda=request.POST.get(
                'descripcion_vivienda'
            ) or None,

            institucion_educativa=request.POST.get(
                'institucion_educativa'
            ) or None,

            programa_estudio=request.POST.get(
                'programa_estudio'
            ) or None,

            beneficiario=request.POST.get(
                'beneficiario'
            ) or None,

            fecha_retiro_definitivo=request.POST.get(
                'fecha_retiro_definitivo'
            ) or None,

            observaciones=request.POST.get(
                'observaciones'
            )

        )

        messages.success(
            request,
            'Retiro de cesantías creado correctamente.'
        )

        return redirect(
            'retiros_cesantias_empleado',
            id=empleado.id
        )

    return render(
        request,
        'rrhh/cesantias/crear_retiro_cesantias.html',
        {
            'empleado': empleado
        }
    )

@login_required
def editar_retiro_cesantias(request, id):

    retiro = get_object_or_404(
        RetiroCesantias,
        id=id
    )

    if request.method == 'POST':

        retiro.tipo_retiro = request.POST.get(
            'tipo_retiro'
        )

        retiro.fondo_cesantias = request.POST.get(
            'fondo_cesantias'
        )

        retiro.fecha_solicitud = request.POST.get(
            'fecha_solicitud'
        )

        retiro.valor_retiro = request.POST.get(
            'valor_retiro'
        )

        retiro.direccion_vivienda = (
            request.POST.get('direccion_vivienda')
            or None
        )

        retiro.descripcion_vivienda = (
            request.POST.get('descripcion_vivienda')
            or None
        )

        retiro.institucion_educativa = (
            request.POST.get('institucion_educativa')
            or None
        )

        retiro.programa_estudio = (
            request.POST.get('programa_estudio')
            or None
        )

        retiro.beneficiario = (
            request.POST.get('beneficiario')
            or None
        )

        retiro.fecha_retiro_definitivo = (
            request.POST.get('fecha_retiro_definitivo')
            or None
        )

        retiro.observaciones = (
            request.POST.get('observaciones')
            or None
        )

        retiro.save()

        messages.success(
            request,
            'Retiro actualizado correctamente.'
        )

        return redirect(
            'retiros_cesantias_empleado',
            id=retiro.empleado.id
        )

    return render(
        request,
        'rrhh/cesantias/editar_retiro_cesantias.html',
        {
            'retiro': retiro
        }
    )

@login_required
def eliminar_retiro_cesantias(request, id):

    retiro = get_object_or_404(
        RetiroCesantias,
        id=id
    )

    empleado_id = retiro.empleado.id

    retiro.delete()

    messages.success(
        request,
        'Retiro eliminado correctamente.'
    )

    return redirect(
        'retiros_cesantias_empleado',
        id=empleado_id
    )

@login_required
def generar_retiro_cesantias(request, id):

    retiro = get_object_or_404(
        RetiroCesantias,
        id=id
    )

    empleado = retiro.empleado

    # Seleccionar plantilla según el tipo
    if retiro.tipo_retiro == 'VIVIENDA':

        ruta_plantilla = os.path.join(
            settings.BASE_DIR,
            'plantillas_word',
            'retiro_cesantias_vivienda.docx'
        )

    elif retiro.tipo_retiro == 'EDUCACION':

        ruta_plantilla = os.path.join(
            settings.BASE_DIR,
            'plantillas_word',
            'retiro_cesantias_estudio.docx'
        )

    else:

        ruta_plantilla = os.path.join(
            settings.BASE_DIR,
            'plantillas_word',
            'retiro_cesantias_definitivo.docx'
        )

    doc = DocxTemplate(
        ruta_plantilla
    )

    valor_letras = (
        num2words(
            float(retiro.valor_retiro),
            lang='es'
        ).capitalize()
        + ' pesos M/CTE'
    )


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

    now = datetime.now()

    dia_actual = now.day
    mes_actual = meses[now.month]
    anio_actual = now.year

    contexto = {

        'dia_actual': dia_actual,
        'mes_actual': mes_actual,
        'anio_actual': anio_actual,

        'fecha_actual': datetime.now().strftime(
            '%d/%m/%Y'
        ),

        'nombre_completo': empleado.nombre_completo,

        'cedula': empleado.documento,

        'tipo_contrato': empleado.get_tipo_contrato_display(),

        'fondo_cesantias': retiro.fondo_cesantias,

        'valor_retiro': formatear_pesos(retiro.valor_retiro),

        'valor_letras': valor_letras,

        # VIVIENDA
        'direccion_vivienda': retiro.direccion_vivienda,

        'descripcion_vivienda': retiro.descripcion_vivienda,

        # EDUCACIÓN
        'institucion_educativa': retiro.institucion_educativa,

        'programa_estudio': retiro.programa_estudio,

        'beneficiario': retiro.beneficiario,

        # RETIRO DEFINITIVO
        'fecha_retiro_definitivo': retiro.fecha_retiro_definitivo,

        'observaciones': retiro.observaciones

    }

    doc.render(
        contexto
    )

    nombre_limpio = limpiar_nombre_archivo(empleado.nombre_completo)

    nombre_archivo = f"Retiro_Cesantias_{nombre_limpio}.docx"

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