from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from core.models import ActaJuntaDirectiva
from core.helpers.word import generar_word, limpiar_nombre_archivo

@login_required
def actas(request):
    actas = ActaJuntaDirectiva.objects.all()
    return render(request, 'gerencia/actas/actas.html', {'actas': actas})

@login_required
def crear_acta(request):
    if request.method == 'POST':
        ActaJuntaDirectiva.objects.create(
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
            proposiciones=request.POST.get('proposiciones', '')
        )
        return redirect('/actas/')

    return render(request, 'gerencia/actas/crear_acta.html')

@login_required
def detalle_acta(request, id):
    acta = ActaJuntaDirectiva.objects.get(id=id)
    return render(request, 'gerencia/actas/detalle_acta.html', {'acta': acta})

@login_required
def editar_acta(request, id):
    acta = ActaJuntaDirectiva.objects.get(id=id)

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
        acta.estado = request.POST['estado']

        acta.save()
        return redirect(f'/actas/{acta.id}/')

    return render(request, 'gerencia/actas/editar_acta.html', {'acta': acta})

@login_required
def eliminar_acta(request, id):
    acta = get_object_or_404(ActaJuntaDirectiva, id=id)

    if request.method == 'POST':
        acta.delete()
        return redirect('/actas/')

    return render(request, 'gerencia/actas/eliminar_acta.html', {'acta': acta})

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