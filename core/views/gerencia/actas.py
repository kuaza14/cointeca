from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from core.models import ActaJuntaDirectiva

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
    acta = ActaJuntaDirectiva.objects.get(id=id)

    if request.method == 'POST':
        acta.delete()
        return redirect('/actas/')

    return render(request, 'gerencia/actas/eliminar_acta.html', {'acta': acta})