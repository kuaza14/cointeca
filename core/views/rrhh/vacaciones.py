from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.http import FileResponse
import os
import json
from django.http import HttpResponse
from django.db.models import Sum, Q
from django.core.paginator import Paginator
from django.contrib import messages


from docxtpl import DocxTemplate
from datetime import timedelta, date
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

    anios_trabajados = (
        date.today() - empleado.fecha_ingreso
    ).days // 365 if empleado.fecha_ingreso else 0

    dias_acumulados = anios_trabajados * 15

    dias_historicos = getattr(empleado, "dias_vacaciones_tomados_historico", 0) or 0

    dias_tomados_total = (
        Vacacion.objects.filter(
            empleado=empleado
        ).aggregate(
            total=Sum('dias_tomados')
        )['total']
        or 0
    ) + dias_historicos

    dias_disponibles = max(0, dias_acumulados - dias_tomados_total)

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
        
        'dias_disponibles': dias_disponibles,
        
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

    tipo = request.GET.get("tipo", "").strip()
    q = request.GET.get("q", "").strip()

    empleados = Empleado.objects.all().order_by("nombre_completo")

    if q:
        empleados = empleados.filter(
            Q(nombre_completo__icontains=q) |
            Q(documento__icontains=q) |
            Q(cargo__icontains=q)
        )

    lista = []

    for empleado in empleados:

        anios_trabajados = (
            date.today() - empleado.fecha_ingreso
        ).days // 365 if empleado.fecha_ingreso else 0

        dias_acumulados = anios_trabajados * 15

        dias_historicos = getattr(empleado, "dias_vacaciones_tomados_historico", 0) or 0

        dias_tomados_sistema = (
            Vacacion.objects.filter(
                empleado=empleado
            ).aggregate(
                total=Sum('dias_tomados')
            )['total']
            or 0
        )

        dias_tomados_total = dias_historicos + dias_tomados_sistema
        dias_disponibles = max(0, dias_acumulados - dias_tomados_total)

        empleado.anios_trabajados = anios_trabajados
        empleado.dias_acumulados = dias_acumulados
        empleado.dias_historicos = dias_historicos
        empleado.dias_tomados_sistema = dias_tomados_sistema
        empleado.total_tomados = dias_tomados_total
        empleado.total_pendientes = dias_disponibles

        # Última solicitud de vacaciones
        empleado.ultima_vacacion = (
            Vacacion.objects.filter(
                empleado=empleado
            )
            .order_by('-fecha_inicio')
            .first()
        )

        # Estado y Badge visual
        hoy = date.today()
        if (
            empleado.ultima_vacacion
            and empleado.ultima_vacacion.fecha_inicio <= hoy
            and empleado.ultima_vacacion.fecha_regreso
            and empleado.ultima_vacacion.fecha_regreso > hoy
        ):
            empleado.estado_vacaciones = "curso"
            empleado.badge_label = "En vacaciones"
            empleado.badge_class = "bg-blue-100 text-blue-800 border border-blue-300"
            empleado.badge_icon = "🏖️"
        elif (
            empleado.ultima_vacacion
            and hoy < empleado.ultima_vacacion.fecha_inicio <= hoy + timedelta(days=15)
        ):
            empleado.estado_vacaciones = "proxima"
            empleado.badge_label = "Próximas"
            empleado.badge_class = "bg-purple-100 text-purple-800 border border-purple-300"
            empleado.badge_icon = "⏳"
        elif dias_disponibles > 0:
            empleado.estado_vacaciones = "pendiente"
            empleado.badge_label = f"{dias_disponibles} d acumulados"
            empleado.badge_class = "bg-amber-100 text-amber-800 border border-amber-300"
            empleado.badge_icon = "⚠️"
        else:
            empleado.estado_vacaciones = "al_dia"
            empleado.badge_label = "Al día (0 acum.)"
            empleado.badge_class = "bg-emerald-100 text-emerald-800 border border-emerald-300"
            empleado.badge_icon = "✅"

        lista.append(empleado)

    hoy = date.today()

    if tipo == "curso":

        lista = [
            e for e in lista
            if e.estado_vacaciones == "curso"
        ]

    elif tipo == "proximas":

        lista = [
            e for e in lista
            if e.estado_vacaciones == "proxima"
        ]

    elif tipo == "pendientes":

        lista = [
            e for e in lista
            if e.total_pendientes > 0
        ]

    elif tipo == "al_dia":

        lista = [
            e for e in lista
            if e.total_pendientes == 0 and e.estado_vacaciones != "curso"
        ]

    elif tipo == "aniversario":

        lista = [
            e for e in lista
            if (
                e.fecha_ingreso
                and e.fecha_ingreso.month == hoy.month
                and e.fecha_ingreso.day >= hoy.day
            )
        ]

    anio_act = hoy.year
    festivos = holidays.Colombia(years=[anio_act - 1, anio_act, anio_act + 1, anio_act + 2])
    festivos_colombia_json = json.dumps([d.isoformat() for d in sorted(festivos.keys())])

    total_registros = len(lista)
    paginator = Paginator(lista, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "rrhh/vacaciones/vacaciones.html",
        {
            "empleados": page_obj,
            "page_obj": page_obj,
            "total_registros": total_registros,
            "tipo": tipo,
            "q": q,
            "festivos_colombia_json": festivos_colombia_json,
        }
    )


@login_required
def ajustar_vacaciones_historicas(request, id):
    """
    Permite registrar o ajustar los días de vacaciones que el empleado ya tomó
    antes de la implementación del software para evitar que se acumulen indebidamente.
    """
    empleado = get_object_or_404(Empleado, id=id)
    if request.method == "POST":
        try:
            dias = int(request.POST.get("dias_historicos", 0))
            if dias < 0:
                dias = 0
            empleado.dias_vacaciones_tomados_historico = dias
            empleado.save()
            messages.success(
                request,
                f"Días de vacaciones históricos de {empleado.nombre_completo} actualizados a {dias} días con éxito."
            )
        except (ValueError, TypeError):
            messages.error(request, "El número de días ingresado no es válido.")

    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or "/rrhh/vacaciones/"
    return redirect(next_url)

def calcular_resumen_empleado_vacacion(emp):
    if not emp:
        return {}
    anios = (date.today() - emp.fecha_ingreso).days // 365 if emp.fecha_ingreso else 0
    acum = anios * 15
    hist = getattr(emp, 'dias_vacaciones_tomados_historico', 0) or 0
    sis = Vacacion.objects.filter(empleado=emp).aggregate(total=Sum('dias_tomados'))['total'] or 0
    tomados = hist + sis
    disponibles = max(0, acum - tomados)
    anios_cubiertos = tomados // 15
    if emp.fecha_ingreso:
        anio_inicio = emp.fecha_ingreso.year + anios_cubiertos
        periodo = f"{anio_inicio} - {anio_inicio + 1}"
    else:
        anio_act = date.today().year
        periodo = f"{anio_act} - {anio_act + 1}"
    return {
        'id': emp.id,
        'nombre': emp.nombre_completo,
        'documento': getattr(emp, 'documento', '') or '',
        'cargo': emp.cargo or 'Colaborador',
        'fecha_ingreso': emp.fecha_ingreso.strftime('%d/%m/%Y') if emp.fecha_ingreso else '—',
        'anios': anios,
        'acumulados': acum,
        'historicos': hist,
        'sistema': sis,
        'tomados': tomados,
        'disponibles': disponibles,
        'periodo_sugerido': periodo,
    }


def calcular_fechas_habiles_vacacion(fecha_inicio, dias_tomados):
    """
    En Cointeca se labora de Lunes a Sábado.
    Solo los Domingos y los festivos oficiales de Colombia son días no hábiles.
    """
    festivos_colombia = holidays.Colombia(years=[
        fecha_inicio.year - 1, fecha_inicio.year, fecha_inicio.year + 1, fecha_inicio.year + 2
    ])

    def es_dia_habil(d):
        if d in festivos_colombia or d.weekday() == 6:  # 6 = Domingo
            return False
        return True

    # Si la fecha de inicio cae en domingo o festivo, avanzar al primer día hábil
    fecha_actual = fecha_inicio
    while not es_dia_habil(fecha_actual):
        fecha_actual += timedelta(days=1)

    fecha_inicio_efectiva = fecha_actual
    contados = 0
    while contados < dias_tomados:
        if es_dia_habil(fecha_actual):
            contados += 1
        if contados < dias_tomados:
            fecha_actual += timedelta(days=1)

    fecha_fin = fecha_actual
    fecha_regreso = fecha_fin + timedelta(days=1)
    while not es_dia_habil(fecha_regreso):
        fecha_regreso += timedelta(days=1)

    return fecha_inicio_efectiva, fecha_fin, fecha_regreso


@login_required
def crear_vacacion(request, id=None):
    empleados = list(Empleado.objects.all().order_by('nombre_completo'))
    empleado = None
    if id:
        empleado = get_object_or_404(Empleado, id=id)

    # Lista de festivos de Colombia para cálculo dinámico en vivo en el navegador
    anio_act = date.today().year
    festivos = holidays.Colombia(years=[anio_act - 1, anio_act, anio_act + 1, anio_act + 2])
    festivos_colombia_json = json.dumps([d.isoformat() for d in sorted(festivos.keys())])

    # Mapa de empleados para interacción reactiva si el usuario cambia el selector
    empleados_dict = {}
    for e in empleados:
        res = calcular_resumen_empleado_vacacion(e)
        empleados_dict[e.id] = res
        e.resumen_vacaciones = res
    empleados_json = json.dumps(empleados_dict)

    if request.method == 'POST':
        if empleado:
            empleado_id = empleado.id
        else:
            empleado_id = request.POST.get('empleado')

        empleado_actual = get_object_or_404(Empleado, id=empleado_id)
        resumen_emp = calcular_resumen_empleado_vacacion(empleado_actual)

        try:
            fecha_inicio = date.fromisoformat(request.POST['fecha_inicio'])
            dias_tomados = int(request.POST['dias_tomados'])
        except (KeyError, ValueError):
            return render(
                request,
                'rrhh/vacaciones/crear_vacacion.html',
                {
                    'empleados': empleados,
                    'empleado': empleado or empleado_actual,
                    'empleados_json': empleados_json,
                    'festivos_colombia_json': festivos_colombia_json,
                    'resumen_seleccionado': resumen_emp,
                    'error': 'Por favor completa una fecha de inicio y una cantidad de días válida.'
                }
            )

        if dias_tomados <= 0:
            return render(
                request,
                'rrhh/vacaciones/crear_vacacion.html',
                {
                    'empleados': empleados,
                    'empleado': empleado or empleado_actual,
                    'empleados_json': empleados_json,
                    'festivos_colombia_json': festivos_colombia_json,
                    'resumen_seleccionado': resumen_emp,
                    'error': 'La cantidad de días de vacaciones debe ser mayor a 0.'
                }
            )

        dias_disponibles = resumen_emp['disponibles']
        if dias_disponibles == 0:
            return render(
                request,
                'rrhh/vacaciones/crear_vacacion.html',
                {
                    'empleados': empleados,
                    'empleado': empleado or empleado_actual,
                    'empleados_json': empleados_json,
                    'festivos_colombia_json': festivos_colombia_json,
                    'resumen_seleccionado': resumen_emp,
                    'error': f'El colaborador {empleado_actual.nombre_completo} no tiene días acumulados pendientes (Saldo disponible: 0 días).'
                }
            )

        if dias_tomados > dias_disponibles:
            return render(
                request,
                'rrhh/vacaciones/crear_vacacion.html',
                {
                    'empleados': empleados,
                    'empleado': empleado or empleado_actual,
                    'empleados_json': empleados_json,
                    'festivos_colombia_json': festivos_colombia_json,
                    'resumen_seleccionado': resumen_emp,
                    'error': f'El colaborador solo tiene {dias_disponibles} días disponibles. No es posible solicitar {dias_tomados} días.'
                }
            )

        # Cálculo de fechas hábiles (Lunes a Sábado en Cointeca)
        fecha_inicio_efectiva, fecha_fin, fecha_regreso = calcular_fechas_habiles_vacacion(
            fecha_inicio, dias_tomados
        )

        # Periodo: si viene vacío, usar el autocalculado por el sistema
        periodo = request.POST.get('periodo', '').strip()
        if not periodo:
            periodo = resumen_emp['periodo_sugerido']

        dias_pendientes = dias_disponibles - dias_tomados

        Vacacion.objects.create(
            empleado=empleado_actual,
            periodo=periodo,
            fecha_inicio=fecha_inicio_efectiva,
            fecha_fin=fecha_fin,
            fecha_regreso=fecha_regreso,
            dias_tomados=dias_tomados,
            dias_pendientes=dias_pendientes,
            observaciones=request.POST.get('observaciones', '').strip()
        )

        messages.success(
            request,
            f'Vacaciones de {empleado_actual.nombre_completo} ({periodo}) registradas exitosamente del {fecha_inicio_efectiva.strftime("%d/%m/%Y")} al {fecha_fin.strftime("%d/%m/%Y")}. Regreso a laborar: {fecha_regreso.strftime("%d/%m/%Y")}.'
        )

        return redirect('vacaciones')

    if empleado:
        resumen_sel = calcular_resumen_empleado_vacacion(empleado)
    elif empleados:
        # Preseleccionar al primer empleado que tenga días disponibles, o al primer empleado de la lista
        emp_con_dias = None
        for e in empleados:
            if empleados_dict.get(e.id, {}).get('disponibles', 0) > 0:
                emp_con_dias = e
                break
        primer_emp = emp_con_dias or empleados[0]
        resumen_sel = calcular_resumen_empleado_vacacion(primer_emp)
    else:
        resumen_sel = None

    return render(
        request,
        'rrhh/vacaciones/crear_vacacion.html',
        {
            'empleados': empleados,
            'empleado': empleado,
            'empleados_json': empleados_json,
            'festivos_colombia_json': festivos_colombia_json,
            'resumen_seleccionado': resumen_sel,
        }
    )


@login_required
def crear_vacacion_empleado(request, id=None):
    return crear_vacacion(request, id=id)

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

    anios_trabajados = (
        date.today() - empleado.fecha_ingreso
    ).days // 365 if empleado.fecha_ingreso else 0

    dias_acumulados = anios_trabajados * 15

    dias_historicos = getattr(empleado, "dias_vacaciones_tomados_historico", 0) or 0

    dias_tomados_sistema = (
        Vacacion.objects.filter(
            empleado=empleado
        ).aggregate(
            total=Sum('dias_tomados')
        )['total']
        or 0
    )

    dias_tomados_total = dias_historicos + dias_tomados_sistema
    dias_disponibles = max(0, dias_acumulados - dias_tomados_total)

    empleado.anios_trabajados = anios_trabajados
    empleado.dias_acumulados = dias_acumulados
    empleado.dias_historicos = dias_historicos
    empleado.dias_tomados_sistema = dias_tomados_sistema
    empleado.total_tomados = dias_tomados_total
    empleado.total_pendientes = dias_disponibles

    anio_act = date.today().year
    festivos = holidays.Colombia(years=[anio_act - 1, anio_act, anio_act + 1, anio_act + 2])
    festivos_colombia_json = json.dumps([d.isoformat() for d in sorted(festivos.keys())])

    return render(
        request,
        'rrhh/vacaciones/vacaciones_empleado.html',
        {
            'empleado': empleado,
            'vacaciones': registros,
            'dias_disponibles': dias_disponibles,
            'festivos_colombia_json': festivos_colombia_json,
        }
    )

@login_required
def editar_vacacion(request, id):
    vacacion = get_object_or_404(
        Vacacion,
        id=id
    )

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or '/rrhh/vacaciones/'

    if request.method == 'POST':
        periodo = request.POST.get('periodo', '').strip() or vacacion.periodo

        try:
            fecha_inicio = date.fromisoformat(request.POST['fecha_inicio'])
            dias_tomados = int(request.POST['dias_tomados'])
        except (KeyError, ValueError):
            messages.error(request, 'Datos de fecha o días de vacaciones no válidos.')
            return redirect(next_url)

        if dias_tomados <= 0:
            messages.error(request, 'La cantidad de días de vacaciones debe ser mayor a 0.')
            return redirect(next_url)

        observaciones = request.POST.get('observaciones', '').strip()

        fecha_inicio_efectiva, fecha_fin, fecha_regreso = calcular_fechas_habiles_vacacion(
            fecha_inicio, dias_tomados
        )

        anios_trabajados = (
            date.today() - vacacion.empleado.fecha_ingreso
        ).days // 365 if vacacion.empleado.fecha_ingreso else 0

        dias_acumulados = anios_trabajados * 15
        dias_historicos = getattr(vacacion.empleado, 'dias_vacaciones_tomados_historico', 0) or 0

        # Días tomados en el sistema excluyendo esta vacación que se está editando
        dias_tomados_sistema_otros = (
            Vacacion.objects.filter(
                empleado=vacacion.empleado
            ).exclude(
                id=vacacion.id
            ).aggregate(
                total=Sum('dias_tomados')
            )['total']
            or 0
        )

        dias_disponibles_con_esta = max(0, dias_acumulados - (dias_historicos + dias_tomados_sistema_otros))

        if dias_tomados > dias_disponibles_con_esta:
            messages.error(
                request,
                f'El colaborador {vacacion.empleado.nombre_completo} solo tiene {dias_disponibles_con_esta} días disponibles para asignar. No es posible asignar {dias_tomados} días.'
            )
            return redirect(next_url)

        dias_pendientes = dias_disponibles_con_esta - dias_tomados

        vacacion.periodo = periodo
        vacacion.fecha_inicio = fecha_inicio_efectiva
        vacacion.fecha_fin = fecha_fin
        vacacion.fecha_regreso = fecha_regreso
        vacacion.dias_tomados = dias_tomados
        vacacion.dias_pendientes = dias_pendientes
        vacacion.observaciones = observaciones
        vacacion.save()

        messages.success(
            request,
            f'Salida de vacaciones de {vacacion.empleado.nombre_completo} ({periodo}) actualizada correctamente: {dias_tomados} días del {fecha_inicio_efectiva.strftime("%d/%m/%Y")} al {fecha_fin.strftime("%d/%m/%Y")}. Regreso: {fecha_regreso.strftime("%d/%m/%Y")}.'
        )
        return redirect(next_url)

    return redirect('vacaciones')

@login_required
def eliminar_vacacion(request, id):
    vacacion = get_object_or_404(
        Vacacion,
        id=id
    )
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or '/rrhh/vacaciones/'

    if request.method == 'POST':
        colaborador = vacacion.empleado.nombre_completo
        dias = vacacion.dias_tomados
        vacacion.delete()
        messages.success(
            request,
            f'Salida de vacaciones de {colaborador} eliminada correctamente. Se reintegraron {dias} días a su saldo disponible.'
        )

    return redirect(next_url)


