from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.http import FileResponse
import os
from django.http import HttpResponse

from docxtpl import DocxTemplate
from datetime import timedelta,date
import holidays

from django.conf import settings

from core.models import Empleado, Vacacion, SolicitudVacaciones

@login_required
def solicitud_vacaciones(request, id):
    """
    Genera un documento Word con la solicitud de vacaciones del empleado
    """
    
    empleado = get_object_or_404(Empleado, id=id)

    # Obtener la última vacación del empleado
    vacacion = Vacacion.objects.filter(
        empleado=empleado
    ).order_by('-fecha_inicio').first()  # Usar order_by en lugar de latest

    # Verificar que existe una vacación registrada
    if not vacacion:
        return HttpResponse(
            "Este empleado no tiene solicitudes de vacaciones registradas."
        )

    # Ruta de la plantilla Word
    ruta_plantilla = os.path.join(
        settings.BASE_DIR,
        'plantillas_word',
        'solicitud_vacaciones.docx'
    )

    # Cargar la plantilla
    doc = DocxTemplate(ruta_plantilla)

    # Preparar el contexto con los datos de la vacación
    contexto = {
        'empleado': empleado,           # Objeto completo - puedes usar {{ empleado.nombre_completo }}, etc
        'vacacion': vacacion,           # Objeto completo
        
        'empleado_area': empleado.area if hasattr(empleado, 'area') else '',
        
        'fecha_solicitud': vacacion.fecha_inicio.strftime('%d/%m/%Y'),
        'fecha_periodo_servido': empleado.fecha_ingreso.strftime('%d/%m/%Y'),
        
        'periodo_desde': vacacion.fecha_inicio.strftime('%d/%m/%Y'),
        'periodo_hasta': vacacion.fecha_fin.strftime('%d/%m/%Y'),
        
        'dias_solicitados': vacacion.dias_tomados,
        
        'vacaciones_desde': vacacion.fecha_inicio.strftime('%d/%m/%Y'),
        'vacaciones_hasta': vacacion.fecha_fin.strftime('%d/%m/%Y'),
        
        'dias_disponibles': vacacion.dias_disponibles,
        
        'nombre_rrhh': 'Gestión RRHH',  # Cambiar según corresponda
    }

    # Renderizar la plantilla con los datos
    doc.render(contexto)

    # Guardar el archivo
    ruta_salida = os.path.join(
        settings.MEDIA_ROOT,
        f'solicitud_vacaciones_{empleado.id}_{vacacion.id}.docx'
    )

    doc.save(ruta_salida)

    # Descargar el archivo
    return FileResponse(
        open(ruta_salida, 'rb'),
        as_attachment=True,
        filename=f'Solicitud_Vacaciones_{empleado.nombre_completo}.docx'
    )


@login_required
def vacaciones_home(request):
    empleados = Empleado.objects.all()

    return render(
        request,
        'rrhh/vacaciones/vacaciones.html',
        {
            'empleados': empleados
        }
    )

@login_required
def vacaciones(request):

    vacaciones = Vacacion.objects.select_related(
        'empleado'
    ).all()


    return render(
        request,
        'rrhh/vacaciones/vacaciones.html',
        {
            'vacaciones': vacaciones
        }
    )

@login_required
def crear_vacacion(request, id=None):

    empleados = Empleado.objects.all()

    empleado = None

    if id:
        empleado = get_object_or_404(
            Empleado,
            id=id
        )

    if request.method == 'POST':

        if empleado:
            empleado_id = empleado.id
        else:
            empleado_id = request.POST['empleado']

        fecha_inicio = date.fromisoformat(
            request.POST['fecha_inicio']
        )

        dias_tomados = int(
            request.POST['dias_tomados']
        )

        festivos_colombia = holidays.Colombia()

        fecha_actual = fecha_inicio
        dias_contados = 0

        while dias_contados < dias_tomados:

            if (
                fecha_actual.weekday() != 6
                and fecha_actual not in festivos_colombia
            ):
                dias_contados += 1

            fecha_actual += timedelta(days=1)

        fecha_fin = fecha_actual - timedelta(days=1)

        fecha_regreso = fecha_fin + timedelta(days=1)

        while (
            fecha_regreso.weekday() == 6
            or fecha_regreso in festivos_colombia
        ):
            fecha_regreso += timedelta(days=1)


        ultima_vacacion = Vacacion.objects.filter(
            empleado_id=empleado_id
        ).order_by(
            '-id'
        ).first()


        if ultima_vacacion:
            dias_disponibles = ultima_vacacion.dias_pendientes
        else:
            dias_disponibles = 15

        # Verificar que no pida más días de los disponibles
        if dias_tomados > dias_disponibles:
            return render(
                request,
                'rrhh/vacaciones/crear_vacacion.html',
                {
                    'empleados': empleados,
                    'error': 'El empleado no tiene suficientes días disponibles.'
                }
            )

        dias_pendientes = dias_disponibles - dias_tomados




        Vacacion.objects.create(
            empleado_id=empleado_id,
            periodo=request.POST['periodo'],
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            fecha_regreso=fecha_regreso,
            dias_disponibles=dias_disponibles,
            dias_tomados=dias_tomados,
            dias_pendientes=dias_pendientes,
            observaciones=request.POST.get(
                'observaciones',
                ''
            )
        )

        return redirect('vacaciones')

    return render(
        request,
        'rrhh/vacaciones/crear_vacacion.html',
        {
            'empleados': empleados,
            'empleado':empleado
        }
    )

@login_required
def crear_vacacion_empleado(request, id=None):

    empleado = get_object_or_404(
        Empleado,
        id=id
    )

    return render(
        request,
        'rrhh/vacaciones/crear_vacacion.html',
        {
            'empleado': empleado
        }
    )

@login_required
def vacaciones_empleado(request, id):

    empleado = get_object_or_404(
        Empleado,
        id=id
    )

    registros = Vacacion.objects.filter(
        empleado=empleado
    ).order_by(
        '-fecha_inicio'
    )

    if registros.exists():
        dias_disponibles = registros.first().dias_pendientes
    else:
        dias_disponibles = 15

    return render(
        request,
        'rrhh/vacaciones/vacaciones_empleado.html',
        {
            'empleado': empleado,
            'vacaciones': registros,
            'dias_disponibles': dias_disponibles
        }
    )