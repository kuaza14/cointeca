from datetime import date

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect

from core.models import Empleado, SuspensionDisciplinaria

from core.models import SuspensionDisciplinaria
from core.helpers.word import generar_word, limpiar_nombre_archivo


@login_required
def suspensiones_disciplinarias_empleado(request, id):
    empleado = get_object_or_404(Empleado, id=id)

    suspensiones = SuspensionDisciplinaria.objects.filter(
        empleado=empleado
    ).order_by('-fecha_creacion')

    return render(
        request,
        'rrhh/suspension_disciplinaria/suspension_disciplinaria.html',
        {
            'empleado': empleado,
            'suspensiones': suspensiones
        }
    )

    
@login_required
def detalle_suspension_disciplinaria(request, id):

    suspension = get_object_or_404(
        SuspensionDisciplinaria,
        id=id
    )

    return render(
        request,
        'rrhh/suspension_disciplinaria/detalle_suspension_disciplinaria.html',
        {
            'suspension': suspension
        }
    )

@login_required
def crear_suspension_disciplinaria(request, id):

    empleado = get_object_or_404(Empleado, id=id)

    if request.method == 'POST':

        suspension = SuspensionDisciplinaria.objects.create(
            empleado=empleado,
            motivo_suspension=request.POST.get('motivo_suspension', ''),
            fecha_falta=request.POST.get('fecha_falta'),
            articulos_infringidos=request.POST.get(
                'articulos_infringidos', ''
            ),
            fecha_inicio_suspension=request.POST.get(
                'fecha_inicio_suspension'
            ),
            fecha_fin_suspension=request.POST.get(
                'fecha_fin_suspension'
            ),
            fecha_reincorporacion=request.POST.get(
                'fecha_reincorporacion'
            ),
            responsabilidad_pecuniaria=request.POST.get(
                'responsabilidad_pecuniaria', ''
            ),
            consecuencia_reincidencia=request.POST.get(
                'consecuencia_reincidencia', ''
            ),
        )

        return redirect(
            'detalle_suspension_disciplinaria',
            id=suspension.id
        )

    return render(
        request,
        'rrhh/suspension_disciplinaria/crear_suspension_disciplinaria.html',
        {
            'empleado': empleado
        }
    )

@login_required
def generar_suspension_disciplinaria(request, id):

    suspension = get_object_or_404(
        SuspensionDisciplinaria,
        id=id
    )

    empleado = suspension.empleado
    hoy = date.today()

    context = {
        # FECHA DEL DOCUMENTO
        'dia_actual': hoy.day,
        'mes_actual': hoy.strftime('%B'),
        'anio_actual': hoy.year,

        # EMPLEADO
        'nombre_empleado': empleado.nombre_completo,
        'documento_empleado': empleado.documento,
        'area_empleado': empleado.area,
        'cargo_empleado': empleado.cargo,

        # SUSPENSIÓN
        'motivo_suspension': suspension.motivo_suspension,
        'fecha_falta': suspension.fecha_falta.strftime('%d/%m/%Y'),
        'articulos_infringidos': suspension.articulos_infringidos,

        'fecha_inicio_suspension':
            suspension.fecha_inicio_suspension.strftime('%d/%m/%Y'),

        'fecha_fin_suspension':
            suspension.fecha_fin_suspension.strftime('%d/%m/%Y'),

        'fecha_reincorporacion':
            suspension.fecha_reincorporacion.strftime('%d/%m/%Y'),

        'responsabilidad_pecuniaria':
            suspension.responsabilidad_pecuniaria or '',

        'consecuencia_reincidencia':
            suspension.consecuencia_reincidencia or '',
    }

    return generar_word(
        'suspension_disciplinaria.docx',
        limpiar_nombre_archivo(
            f'Suspension_Disciplinaria_{empleado.nombre_completo}.docx'
        ),
        context
    )