from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from core.models import Empleado, ContratoAprendizaje


@login_required
def contratos_aprendiz_empleado(request, id):

    empleado = get_object_or_404(
        Empleado,
        id=id
    )

    contratos = ContratoAprendizaje.objects.filter(
        empleado=empleado
    ).order_by('-fecha_inicio')

    return render(
        request,
        'rrhh/contratos_aprendiz/contratos_aprendiz_empleado.html',
        {
            'empleado': empleado,
            'contratos': contratos
        }
    )


@login_required
def crear_contrato_aprendiz(request, id):

    empleado = get_object_or_404(
        Empleado,
        id=id
    )

    if request.method == 'POST':
        
        institucion=request.POST["institucion"]

        ContratoAprendizaje.objects.create(

            empleado=empleado,

            institucion=institucion,

            especialidad=request.POST.get('especialidad', ''),

            numero_grupo=request.POST.get('numero_grupo', ''),

            modalidad=request.POST.get('modalidad', ''),

            fecha_inicio=request.POST['fecha_inicio'],

            fecha_fin=request.POST['fecha_fin'],

            fecha_inicio_lectiva=request.POST['fecha_inicio_lectiva'],

            fecha_fin_lectiva=request.POST['fecha_fin_lectiva'],

            fecha_inicio_practica=request.POST['fecha_inicio_practica'],

            fecha_fin_practica=request.POST['fecha_fin_practica'],

            porcentaje_apoyo=request.POST['porcentaje_apoyo'],

        )

        messages.success(
            request,
            '✅ Contrato de aprendizaje registrado correctamente.'
        )

        return redirect(
            f'/rrhh/empleados/{id}/contrato_aprendiz/'
        )

    return render(
        request,
        'rrhh/contratos_aprendiz/crear_contrato_aprendiz.html',
        {
            'empleado': empleado
        }
    )


@login_required
def editar_contrato_aprendiz(request, id):

    contrato = get_object_or_404(
        ContratoAprendizaje,
        id=id
    )

    if request.method == 'POST':

        contrato.institucion = request.POST["institucion"]

        contrato.especialidad = request.POST.get(
            'especialidad',
            ''
        )

        contrato.numero_grupo = request.POST.get(
            'numero_grupo',
            ''
        )

        contrato.modalidad = request.POST.get(
            'modalidad',
            ''
        )

        contrato.fecha_inicio = request.POST['fecha_inicio']

        contrato.fecha_fin = request.POST['fecha_fin']

        contrato.fecha_inicio_lectiva = request.POST['fecha_inicio_lectiva']

        contrato.fecha_fin_lectiva = request.POST['fecha_fin_lectiva']

        contrato.fecha_inicio_practica = request.POST['fecha_inicio_practica']

        contrato.fecha_fin_practica = request.POST['fecha_fin_practica']

        contrato.porcentaje_apoyo = request.POST['porcentaje_apoyo']

        contrato.save()

        messages.success(
            request,
            '✅ Contrato de aprendizaje actualizado correctamente.'
        )

        return redirect(
            f'/rrhh/empleados/{contrato.empleado.id}/contrato_aprendiz/'
        )

    return render(
        request,
        'rrhh/contratos_aprendiz/editar_contrato_aprendiz.html',
        {
            'empleado': contrato.empleado,
            'contrato': contrato
        }
    )


@login_required
def eliminar_contrato_aprendiz(request, id):

    contrato = get_object_or_404(
        ContratoAprendizaje,
        id=id
    )

    empleado_id = contrato.empleado.id

    contrato.delete()

    messages.success(
        request,
        '✅ Contrato de aprendizaje eliminado correctamente.'
    )

    return redirect(
        f'/rrhh/empleados/{empleado_id}/contrato_aprendiz/'
    )


@login_required
def generar_contrato_aprendiz(request, id):

    contrato = get_object_or_404(
        ContratoAprendizaje,
        id=id
    )

    # Aquí luego haremos el Word

    pass