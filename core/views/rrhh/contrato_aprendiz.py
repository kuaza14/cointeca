from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import date

from core.models import Empleado, ContratoAprendizaje
from core.helpers.word import generar_word, limpiar_nombre_archivo

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

            nit_institucion=request.POST.get('nit_institucion', ''),

            centro_formacion=request.POST.get('centro_formacion', ''),

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

        contrato.nit_institucion = request.POST.get(
            'nit_institucion',
            ''
        )

        contrato.centro_formacion = request.POST.get(
            'centro_formacion',
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

    empleado = contrato.empleado

    hoy = date.today()

    # Duración aproximada del contrato en meses
    duracion_meses = (
        (contrato.fecha_fin.year - contrato.fecha_inicio.year) * 12
        + contrato.fecha_fin.month
        - contrato.fecha_inicio.month
    )

    context = {

        # ==========================================
        # DATOS EMPRESA
        # ==========================================
        'empresa': 'COMERCIALIZADORA DE INGENIERIA & TECNOLOGIAS APLICADAS SAS – COINTECA SAS',
        'nit_empresa': '900.768.648',
        'direccion_empresa': '',  # Completar dato real
        'telefono_empresa': '',   # Completar dato real
        'representante_legal': '',  # Completar dato real
        'cargo_representante': 'Representante Legal',
        'documento_representante': '',  # Completar dato real
        'ciudad_expedicion_representante': '',

        # ==========================================
        # DATOS DEL APRENDIZ
        # ==========================================
        'nombre_aprendiz': empleado.nombre_completo,
        'documento_aprendiz': empleado.documento,
        'ciudad_expedicion_aprendiz': empleado.ciudad_expedicion,
        'fecha_nacimiento': empleado.fecha_nacimiento.strftime('%d/%m/%Y'),

        'direccion_aprendiz': empleado.direccion,
        'barrio_aprendiz': empleado.barrio,
        'ciudad_residencia': empleado.ciudad_residencia,
        'telefono_aprendiz': empleado.telefono,
        'correo_aprendiz': empleado.correo,
        'estrato_aprendiz': empleado.estrato,

        # ==========================================
        # SEGURIDAD SOCIAL
        # ==========================================
        'eps': empleado.eps or '',
        'arl': empleado.arl or '',
        'afp': empleado.afp or '',
        'cesantias': empleado.cesantias or '',

        # ==========================================
        # DATOS INSTITUCIÓN
        # ==========================================
        'institucion': contrato.institucion,
        'nit_institucion': contrato.nit_institucion,
        'centro_formacion': contrato.centro_formacion,

        # ==========================================
        # DATOS DEL CONTRATO
        # ==========================================
        'especialidad': contrato.especialidad,
        'numero_grupo': contrato.numero_grupo,
        'modalidad': contrato.modalidad,
        'porcentaje_apoyo': contrato.porcentaje_apoyo,
        'duracion_meses': duracion_meses,

        # Fechas completas
        'fecha_inicio': contrato.fecha_inicio.strftime('%d/%m/%Y'),
        'fecha_fin': contrato.fecha_fin.strftime('%d/%m/%Y'),

        'fecha_inicio_lectiva': contrato.fecha_inicio_lectiva.strftime('%d/%m/%Y'),
        'fecha_fin_lectiva': contrato.fecha_fin_lectiva.strftime('%d/%m/%Y'),

        'fecha_inicio_practica': contrato.fecha_inicio_practica.strftime('%d/%m/%Y'),
        'fecha_fin_practica': contrato.fecha_fin_practica.strftime('%d/%m/%Y'),

        # Fecha inicio separada
        'dia_inicio': contrato.fecha_inicio.day,
        'mes_inicio': contrato.fecha_inicio.strftime('%B'),
        'anio_inicio': contrato.fecha_inicio.year,

        # Fecha final separada
        'dia_fin': contrato.fecha_fin.day,
        'mes_fin': contrato.fecha_fin.strftime('%B'),
        'anio_fin': contrato.fecha_fin.year,

        # ==========================================
        # FECHA DE GENERACIÓN / FIRMA
        # ==========================================
        'dia_firma': hoy.day,
        'mes_firma': hoy.strftime('%B'),
        'anio_firma': hoy.year,
        'ciudad_firma': empleado.ciudad_residencia,
    }

    return generar_word(
        nombre_plantilla='contrato_aprendiz.docx',
        nombre_archivo=limpiar_nombre_archivo(
            f'Contrato_Aprendizaje_{empleado.nombre_completo}.docx'
        ),
        contexto=context
    )