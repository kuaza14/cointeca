from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from core.models import ActaJuntaDirectiva
from core.helpers.word import generar_word, limpiar_nombre_archivo

@login_required
def actas(request):
    actas = ActaJuntaDirectiva.objects.all().order_by('-fecha', '-id')
    total_actas = actas.count()
    actas_custodiadas = actas.filter(archivo_firmado__isnull=False).exclude(archivo_firmado='').count()
    actas_aprobadas = actas.filter(estado='aprobada').count()
    actas_borrador = actas.filter(estado='borrador').count()
    ultima_sesion = actas.first()
    porcentaje_custodia = round((actas_custodiadas / total_actas * 100), 1) if total_actas > 0 else 0
    
    return render(request, 'gerencia/actas/actas.html', {
        'actas': actas,
        'total_actas': total_actas,
        'actas_custodiadas': actas_custodiadas,
        'actas_aprobadas': actas_aprobadas,
        'actas_borrador': actas_borrador,
        'porcentaje_custodia': porcentaje_custodia,
        'ultima_sesion': ultima_sesion,
    })

@login_required
def crear_acta(request):
    if request.method == 'POST':
        archivo_firmado = request.FILES.get('archivo_firmado')
        acta = ActaJuntaDirectiva.objects.create(
            numero_acta=request.POST['numero_acta'],
            nombre_entidad=request.POST['nombre_entidad'],
            nit=request.POST['nit'],
            fecha=request.POST['fecha'],
            hora_inicio=request.POST['hora_inicio'],
            lugar=request.POST['lugar'],
            presidente=request.POST['presidente'],
            secretario=request.POST['secretario'],
            orden_del_dia=request.POST['orden_del_dia'],
            desarrollo=request.POST['desarrollo'],
            proposiciones=request.POST.get('proposiciones', ''),
            archivo_firmado=archivo_firmado,
        )
        return redirect('detalle_acta', id=acta.id)

    return render(request, 'gerencia/actas/crear_acta.html')

@login_required
def detalle_acta(request, id):
    acta = get_object_or_404(ActaJuntaDirectiva, id=id)
    return render(request, 'gerencia/actas/detalle_acta.html', {'acta': acta})

@login_required
def editar_acta(request, id):
    acta = get_object_or_404(ActaJuntaDirectiva, id=id)

    if request.method == 'POST':
        acta.numero_acta = request.POST['numero_acta']
        acta.nombre_entidad = request.POST['nombre_entidad']
        acta.nit = request.POST['nit']
        acta.fecha = request.POST['fecha']
        acta.hora_inicio = request.POST['hora_inicio']
        acta.lugar = request.POST['lugar']
        acta.presidente = request.POST['presidente']
        acta.secretario = request.POST['secretario']
        acta.orden_del_dia = request.POST['orden_del_dia']
        acta.desarrollo = request.POST['desarrollo']
        acta.proposiciones = request.POST.get('proposiciones', '')
        acta.estado = request.POST.get('estado', acta.estado)

        if request.FILES.get('archivo_firmado'):
            acta.archivo_firmado = request.FILES.get('archivo_firmado')
        elif request.POST.get('eliminar_archivo_firmado'):
            if acta.archivo_firmado:
                acta.archivo_firmado.delete(save=False)
            acta.archivo_firmado = None

        acta.save()
        return redirect('detalle_acta', id=acta.id)

    return render(request, 'gerencia/actas/editar_acta.html', {'acta': acta})

@login_required
def eliminar_acta(request, id):
    acta = get_object_or_404(ActaJuntaDirectiva, id=id)

    if request.method == 'POST':
        acta.delete()
        return redirect('/actas/')

    return render(request, 'gerencia/actas/eliminar_acta.html', {'acta': acta})

@login_required
def imprimir_acta(request, id):
    """
    Vista oficial para impresión directa y generación de PDF en el navegador
    con formato institucional idéntico a GR-FR-01.
    """
    acta = get_object_or_404(ActaJuntaDirectiva, id=id)
    return render(request, 'gerencia/actas/imprimir_acta.html', {
        'acta': acta,
    })

@login_required
def exportar_acta_word(request, id):
    acta = get_object_or_404(ActaJuntaDirectiva, id=id)
    nombre_limpio = limpiar_nombre_archivo(f"Acta_Junta_Directiva_{acta.numero_acta}.docx")
    contexto = {
        'numero_acta': acta.numero_acta,
        'nombre_entidad': acta.nombre_entidad or "COINTECA S.A.S.",
        'nit': acta.nit or "",
        'fecha': acta.fecha.strftime("%d/%m/%Y") if acta.fecha else "",
        'hora_inicio': acta.hora_inicio.strftime("%I:%M %p") if acta.hora_inicio else "",
        'lugar': acta.lugar or "",
        'presidente': acta.presidente or "",
        'secretario': acta.secretario or "",
        'orden_del_dia': acta.orden_del_dia or "",
        'desarrollo': acta.desarrollo or "",
        'proposiciones': acta.proposiciones or "Sin proposiciones adicionales.",
    }
    return generar_word("acta_junta_directiva.docx", nombre_limpio, contexto)