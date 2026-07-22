from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Avg, Count

from core.models import (
    Empleado,
    SaludEmpleado,
    DotacionEmpleado,
    DocumentoEmpleado,
    AsignacionEquipo,
)

@login_required
def rrhh_home(request):
    return render(request, 'rrhh/rrhh.html')

@login_required
def crear_empleado(request):
    if request.method == 'POST':
        try:

            salario = request.POST.get('salario', '').replace('.', '').replace(',', '')

            if not salario:
                salario = 0

            empleado = Empleado.objects.create(
                foto=request.FILES.get('foto'),
                nombre_completo=request.POST['nombre_completo'],
                documento=request.POST['documento'],
                ciudad_expedicion=request.POST.get('ciudad_expedicion', ''),
                fecha_nacimiento=request.POST.get('fecha_nacimiento') or None,
                nacionalidad=request.POST['nacionalidad'],
                direccion=request.POST['direccion'],
                ciudad_residencia=request.POST.get('ciudad_residencia', ''),
                barrio=request.POST.get('barrio', ''),
                estrato=request.POST.get('estrato')or None,
                telefono=request.POST['telefono'],
                correo=request.POST['correo'],
                contacto_emergencia=request.POST.get('contacto_emergencia', ''),
                telefono_emergencia=request.POST.get('telefono_emergencia', ''),
                parentesco_emergencia=request.POST.get('parentesco_emergencia', ''),
                cargo=request.POST['cargo'],
                area=request.POST['area'],
                nivel_academico=request.POST['nivel_academico'],
                profesion=request.POST.get('profesion', ''),
                habilidades=request.POST.get('habilidades', ''),
                idiomas=request.POST['idiomas'],
                fecha_ingreso=request.POST.get('fecha_ingreso') or None,
                fecha_finalizacion=request.POST.get('fecha_finalizacion') or None,
                tipo_contrato=request.POST['tipo_contrato'],
                salario=int(salario),
                jornada=request.POST['jornada'],
                jefe=request.POST['jefe']
            )

            SaludEmpleado.objects.create(
                empleado=empleado,
                grupo_sanguineo=request.POST['grupo_sanguineo'],
                eps=request.POST['eps'],
                pension=request.POST['pension'],
                cesantias=request.POST['cesantias'],
                arl=request.POST['arl']
            )
            messages.success(
                request,
                f'✅ El empleado {empleado.nombre_completo} fue registrado correctamente.'
            )

            return redirect('/rrhh/empleados/')

        except IntegrityError:
            return render(request, 'rrhh/empleados/crear_empleado.html', {
                'error': '⚠️ Ya existe un empleado con ese documento'
            })
            
    return render(request, 'rrhh/empleados/crear_empleado.html')


@login_required
def empleados(request):
    query = request.GET.get('q')

    if query:
        lista = Empleado.objects.filter(
            Q(documento__icontains=query) |
            Q(nombre_completo__icontains=query)
        )
    else:
        lista = Empleado.objects.all()

    # 📊 ESTADÍSTICAS
    total = lista.count()
    promedio_salario = lista.aggregate(Avg('salario'))['salario__avg']
    por_cargo = lista.values('cargo').annotate(total=Count('id'))

    return render(request, 'rrhh/empleados/empleados.html', {
        'empleados': lista,
        'query': query,
        'total': total,
        'promedio_salario': promedio_salario,
        'por_cargo': por_cargo
    })

@login_required
def eliminar_empleado(request, id):
    empleado = get_object_or_404(Empleado, id=id)

    if request.method == 'POST':
        empleado.delete()
        return redirect('/rrhh/empleados/')

    return redirect('/rrhh/empleados/')

@login_required
def detalle_empleado(request, id):
    empleado = Empleado.objects.get(id=id)

    salud = None
    try:
        salud = empleado.saludempleado
    except:
        pass

    dotaciones = DotacionEmpleado.objects.filter(empleado=empleado)

    equipos = AsignacionEquipo.objects.filter(empleado=empleado)

    documentos = DocumentoEmpleado.objects.filter(empleado=empleado)

    editando = request.GET.get('edit')

    if request.method == 'POST':

    # VALIDAR CAMPOS OBLIGATORIOS
        campos_obligatorios = {
            'nombre_completo': 'Nombre completo',
            'documento': 'Documento',
            'salario': 'Salario',
        }

        campos_faltantes = []

        for campo, nombre in campos_obligatorios.items():
            if not request.POST.get(campo, '').strip():
                campos_faltantes.append(nombre)

        # Si hay campos vacíos, mostrar mensaje y regresar a editar
        if campos_faltantes:
            messages.error(
                request,
                '⚠️ Debes completar: ' + ', '.join(campos_faltantes)
            )

            return redirect(f'/rrhh/empleados/{id}/?edit=1')


        # TU CÓDIGO CONTINÚA NORMALMENTE DESDE AQUÍ
        documento = request.POST['documento']

        # VALIDAR DUPLICADO
        existe = Empleado.objects.filter(
            documento=documento
        ).exclude(id=id).exists()

        salario = request.POST['salario'].replace('.', '').replace(',', '')

        if existe:
            return render(request, 'rrhh/empleados/detalle_empleado.html', {
                'empleado': empleado,
                'salud': salud,
                'dotaciones': dotaciones,
                'equipos': equipos,
                'documentos': documentos,
                'editando': True,
                'error': '⚠️ Esta cédula ya está registrada'
            })

        # ACTUALIZAR DATOS
        empleado.nombre_completo = request.POST['nombre_completo']
        empleado.documento = documento
        empleado.ciudad_expedicion = request.POST['ciudad_expedicion']
        empleado.fecha_nacimiento = request.POST['fecha_nacimiento']
        empleado.nacionalidad = request.POST['nacionalidad']
        empleado.direccion = request.POST['direccion']
        empleado.barrio = request.POST.get('barrio', '')
        estrato = request.POST.get('estrato', '').strip()
        if estrato:
            empleado.estrato = int(estrato)
        empleado.ciudad_residencia = request.POST['ciudad_residencia']
        empleado.telefono = request.POST['telefono']
        empleado.correo = request.POST['correo']

        empleado.cargo = request.POST['cargo']
        empleado.area = request.POST['area']
        empleado.nivel_academico = request.POST['nivel_academico']
        empleado.profesion = request.POST['profesion']
        empleado.habilidades = request.POST['habilidades']
        empleado.idiomas = request.POST['idiomas']

        empleado.fecha_ingreso = request.POST['fecha_ingreso']
        empleado.fecha_finalizacion = request.POST.get('fecha_finalizacion') or None
        empleado.tipo_contrato = request.POST['tipo_contrato']
        empleado.salario = int(salario)
        empleado.jornada = request.POST['jornada']
        empleado.jefe = request.POST['jefe']

        # CONTACTO EMERGENCIA
        nuevo_contacto = request.POST.get('contacto_emergencia', '').strip()
        nuevo_telefono = request.POST.get('telefono_emergencia', '').strip()
        nuevo_parentesco = request.POST.get('parentesco_emergencia', '').strip()

        if nuevo_contacto:
            empleado.contacto_emergencia = nuevo_contacto

        if nuevo_telefono:
            empleado.telefono_emergencia = nuevo_telefono

        if nuevo_parentesco:
            empleado.parentesco_emergencia = nuevo_parentesco
        

        # OBSERVACIONES
        empleado.observaciones = request.POST.get('observaciones', "")

        # FOTO DEL EMPLEADO
        if request.POST.get('eliminar_foto'):
            empleado.foto.delete(save=False)
            empleado.foto = None

        elif request.FILES.get('foto'):
            # Elimina la foto anterior antes de guardar la nueva
            if empleado.foto:
                empleado.foto.delete(save=False)

            empleado.foto = request.FILES['foto']

        empleado.save()

        # Actualizar o crear SaludEmpleado
        if salud:
            salud.grupo_sanguineo = request.POST.get('salud_grupo_sanguineo', '')
            salud.eps = request.POST.get('salud_eps', '')
            salud.pension = request.POST.get('salud_pension', '')
            salud.arl = request.POST.get('salud_arl', '')
            salud.alergias = request.POST.get('salud_alergias', '')
            salud.save()
        else:
            SaludEmpleado.objects.create(
                empleado=empleado,
                grupo_sanguineo=request.POST.get('salud_grupo_sanguineo', ''),
                eps=request.POST.get('salud_eps', ''),
                pension=request.POST.get('salud_pension', ''),
                arl=request.POST.get('salud_arl', ''),
                alergias=request.POST.get('salud_alergias', ''),
                contacto_emergencia=request.POST.get('salud_contacto_emergencia', ''),
                telefono_emergencia=request.POST.get('salud_telefono_emergencia', '')
            )

        messages.success(request, '✅ Empleado actualizado correctamente')

        return redirect(f'/rrhh/empleados/{id}/')

    return render(request, 'rrhh/empleados/detalle_empleado.html', {
        'empleado': empleado,
        'salud': salud,
        'dotaciones': dotaciones,
        'equipos': equipos,
        'documentos': documentos,
        'editando': editando
        
    })

@login_required
def agregar_dotacion(request, id):

    empleado = Empleado.objects.get(id=id)

    if request.method == 'POST':

        elementos = request.POST.getlist('elementos[]')
        descripciones = request.POST.getlist('descripciones[]')
        fecha_entrega = request.POST.get('fecha_entrega')

        for i in range(len(elementos)):

            DotacionEmpleado.objects.create(
                empleado=empleado,
                elemento=elementos[i],
                descripcion=descripciones[i],
                fecha_entrega=fecha_entrega
            )

        return redirect('detalle_empleado', id=empleado.id)

    return render(request, 'rrhh/empleados/agregar_dotacion.html', {'empleado': empleado})

@login_required
def editar_dotacion_empleado(request, id):
    dotacion = get_object_or_404(DotacionEmpleado, id=id)

    if request.method == 'POST':
        dotacion.elemento = request.POST.get('elemento', '')
        dotacion.descripcion = request.POST.get('descripcion', '')
        dotacion.save()

        messages.success(
            request,
            '✅ Dotación actualizada correctamente.'
        )

    return redirect(f'/rrhh/empleados/{dotacion.empleado.id}/')

@login_required
def eliminar_dotacion_empleado(request, id):
    dotacion = get_object_or_404(DotacionEmpleado, id=id)

    empleado_id = dotacion.empleado.id

    if request.method == 'POST':
        dotacion.delete()
        messages.success(
            request,
            '✅ Dotación eliminada correctamente.'
        )

    return redirect(f'/rrhh/empleados/{empleado_id}/')
@login_required
def subir_documento(request, id):

    empleado = Empleado.objects.get(id=id)

    if request.method == 'POST':

        DocumentoEmpleado.objects.create(
            empleado=empleado,
            nombre=request.POST['nombre'],
            archivo=request.FILES['archivo']
        )

        messages.success(request, '✅ Documento subido correctamente')

        return redirect(f'/rrhh/empleados/{id}/')

    return render(request, 'rrhh/empleados/subir_documento.html', {
        'empleado': empleado
    })

@login_required
def eliminar_documento(request, id):

    documento = DocumentoEmpleado.objects.get(id=id)

    empleado_id = documento.empleado.id

    documento.delete()

    messages.success(
        request,
        '🗑️ Documento eliminado correctamente'
    )

    return redirect(f'/rrhh/empleados/{empleado_id}/')