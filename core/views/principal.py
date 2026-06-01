from django.shortcuts import render, redirect
from django.db.models import Avg, Count, Sum
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from core.models import (
    CajaMenor, 
    MovimientoCajaMenor, 
    IndicadorEstrategico, 
    SeguimientoIndicador, 
    ActaJuntaDirectiva, 
    ProyectoFacturacion, 
    SeguimientoFacturacion, 
    Empleado, 
    DotacionEmpleado,
    SaludEmpleado,
    AsignacionEquipo,
    ActaEntregaEquipo,
    InventarioEquipo,
    DocumentoEmpleado,

)
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from django.contrib import messages
from django.http import HttpResponse
from django.http import FileResponse
from weasyprint import HTML
from django.template.loader import render_to_string
from docxtpl import DocxTemplate
from docx2pdf import convert
import os
import tempfile
from django.conf import settings
from docx import Document
from datetime import date


# Vista de inicio 
def inicio(request):
    return render(request, 'inicio.html')

# Vista de login
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('/dashboard/')  
        else:
            return render(request, 'login.html', {'error': 'Usuario o contraseña incorrectos'})

    return render(request, 'login.html')

# Vista del dashboard
@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

# Vista para la caja menor
@login_required 
def caja_menor(request):
    cajas = CajaMenor.objects.all()
    return render(request, 'caja_menor.html', {'cajas': cajas})

@login_required
def detalle_caja(request, id):
    caja = CajaMenor.objects.get(id=id)
    movimientos = caja.movimientocajamenor_set.all()

    return render(request, 'detalle_caja.html', {
        'caja': caja,
        'movimientos': movimientos
    })

@login_required
def agregar_movimiento(request, id):
    caja = CajaMenor.objects.get(id=id)

    if request.method == 'POST':
        MovimientoCajaMenor.objects.create(
            caja=caja,
            fecha=request.POST['fecha'],
            numero_factura=request.POST['numero_factura'],
            nit=request.POST['nit'],
            pagado_a=request.POST['pagado_a'],
            concepto=request.POST['concepto'],
            valor=request.POST['valor'].replace(',', '').replace('.', '')
        )

        return redirect(f'/caja-menor/{id}/')

    return render(request, 'agregar_movimiento.html', {'caja': caja})

@login_required
def eliminar_movimiento(request, id):
    movimiento = get_object_or_404(MovimientoCajaMenor, id=id)
    caja_id = movimiento.caja.id

    movimiento.delete()
    caja.calcular_totales()

    return redirect(f'/caja-menor/{caja_id}/')

@login_required
def editar_movimiento(request, id):
    movimiento = MovimientoCajaMenor.objects.get(id=id)

    if request.method == 'POST':
        movimiento.fecha = request.POST['fecha']
        movimiento.numero_factura = request.POST['numero_factura']
        movimiento.nit = request.POST['nit']
        movimiento.pagado_a = request.POST['pagado_a']
        movimiento.concepto = request.POST['concepto']
        movimiento.valor = request.POST['valor'].replace(',', '').replace('.', '')
        movimiento.save()
        movimiento.caja.calcular_totales()

        return redirect(f'/caja-menor/{movimiento.caja.id}/')

    return render(request, 'editar_movimiento.html', {'m': movimiento})

@login_required
def actas(request):
    actas = ActaJuntaDirectiva.objects.all()
    return render(request, 'actas.html', {'actas': actas})

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

    return render(request, 'crear_acta.html')

@login_required
def detalle_acta(request, id):
    acta = ActaJuntaDirectiva.objects.get(id=id)
    return render(request, 'detalle_acta.html', {'acta': acta})

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

    return render(request, 'editar_acta.html', {'acta': acta})

@login_required
def eliminar_acta(request, id):
    acta = ActaJuntaDirectiva.objects.get(id=id)

    if request.method == 'POST':
        acta.delete()
        return redirect('/actas/')

    return render(request, 'eliminar_acta.html', {'acta': acta})

# Vistas de Indicadores Estratégicos
@login_required
def indicadores(request):
    items = IndicadorEstrategico.objects.all().order_by('perspectiva')
    return render(request, 'indicadores.html', {'indicadores': items})

@login_required
def crear_indicador(request):
    if request.method == 'POST':
        IndicadorEstrategico.objects.create(
            perspectiva=request.POST['perspectiva'],
            nombre=request.POST['nombre'],
            definicion=request.POST['definicion'],
            meta_anual=request.POST['meta_anual'],
            frecuencia=request.POST['frecuencia'],
        )
        return redirect('/indicadores/')
    return render(request, 'crear_indicador.html')

@login_required
def detalle_indicador(request, id):
    indicador = get_object_or_404(IndicadorEstrategico, id=id)
    seguimientos = indicador.seguimientoindicador_set.all().order_by('-fecha')
    return render(request, 'detalle_indicador.html', {
        'indicador': indicador,
        'seguimientos': seguimientos
    })

@login_required
def agregar_seguimiento(request, id):
    indicador = get_object_or_404(IndicadorEstrategico, id=id)
    if request.method == 'POST':
        SeguimientoIndicador.objects.create(
            indicador=indicador,
            fecha=request.POST['fecha'],
            valor_obtenido=request.POST['valor_obtenido'],
            observaciones=request.POST.get('observaciones', '')
        )
        return redirect(f'/indicadores/{id}/')
    return render(request, 'agregar_seguimiento.html', {'indicador': indicador})

@login_required
def eliminar_indicador(request, id):
    indicador = get_object_or_404(IndicadorEstrategico, id=id)
    indicador.delete()
    return redirect('/indicadores/')

@login_required
def editar_indicador(request, id):
    indicador = get_object_or_404(IndicadorEstrategico, id=id)

    if request.method == 'POST':
        indicador.perspectiva = request.POST['perspectiva']
        indicador.nombre = request.POST['nombre']
        indicador.definicion = request.POST['definicion']
        indicador.meta_anual = request.POST['meta_anual']
        indicador.frecuencia = request.POST['frecuencia']
        indicador.save()
        return redirect(f'/indicadores/{id}/')

    return render(request, 'editar_indicador.html', {'indicador': indicador})

@login_required
def eliminar_seguimiento(request, id):
    seguimiento = get_object_or_404(SeguimientoIndicador, id=id)
    indicador_id = seguimiento.indicador.id
    seguimiento.delete()
    return redirect(f'/indicadores/{indicador_id}/')

@login_required
def editar_seguimiento(request, id):    
    seguimiento = get_object_or_404(SeguimientoIndicador, id=id)

    if request.method == 'POST':
        seguimiento.fecha = request.POST['fecha']
        seguimiento.valor_obtenido = request.POST['valor_obtenido']
        seguimiento.observaciones = request.POST.get('observaciones', '')
        seguimiento.save()
        return redirect(f'/indicadores/{seguimiento.indicador.id}/')

    return render(request, 'editar_seguimiento.html', {'seguimiento': seguimiento})

# Vistas de Facturación
@login_required
def facturacion(request):
    proyectos = ProyectoFacturacion.objects.filter(activo=True)
    seguimientos = SeguimientoFacturacion.objects.all().order_by('anio', 'mes')
    return render(request, 'facturacion.html', {
        'proyectos': proyectos,
        'seguimientos': seguimientos
    })

@login_required
def crear_proyecto(request):
    if request.method == 'POST':
        ProyectoFacturacion.objects.create(
            nombre=request.POST['nombre']
        )
        return redirect('/facturacion/')
    return render(request, 'crear_proyecto.html')

@login_required
def registrar_facturacion(request):
    proyectos = ProyectoFacturacion.objects.filter(activo=True)
    if request.method == 'POST':
        SeguimientoFacturacion.objects.create(
            mes=request.POST['mes'],
            anio=request.POST['anio'],
            meta_facturacion=request.POST['meta_facturacion'].replace(',', '').replace('.', ''),
            facturacion_real=request.POST['facturacion_real'].replace(',', '').replace('.', ''),
            proyecto_id=request.POST['proyecto']
        )
        return redirect('/facturacion/')
    return render(request, 'registrar_facturacion.html', {'proyectos': proyectos})

@login_required
def eliminar_facturacion(request, id):
    seguimiento = get_object_or_404(SeguimientoFacturacion, id=id)
    seguimiento.delete()
    return redirect('/facturacion/')

@login_required
def editar_facturacion(request, id):
    seguimiento = get_object_or_404(SeguimientoFacturacion, id=id)
    proyectos = ProyectoFacturacion.objects.filter(activo=True)
    if request.method == 'POST':
        seguimiento.mes = request.POST['mes']
        seguimiento.anio = request.POST['anio']
        seguimiento.meta_facturacion = request.POST['meta_facturacion'].replace(',', '').replace('.', '')
        seguimiento.facturacion_real = request.POST['facturacion_real'].replace(',', '').replace('.', '')
        seguimiento.proyecto_id = request.POST['proyecto']
        seguimiento.save()
        return redirect('/facturacion/')
    return render(request, 'editar_facturacion.html', {
        'seguimiento': seguimiento,
        'proyectos': proyectos
    })

@login_required
def empleados(request):
    query = request.GET.get('q')

    if query:
        lista = Empleado.objects.filter(documento__icontains=query)
    else:
        lista = Empleado.objects.all()

    # 📊 ESTADÍSTICAS
    total = lista.count()
    promedio_salario = lista.aggregate(Avg('salario'))['salario__avg']
    por_cargo = lista.values('cargo').annotate(total=Count('id'))

    return render(request, 'rrhh/empleados.html', {
        'empleados': lista,
        'query': query,
        'total': total,
        'promedio_salario': promedio_salario,
        'por_cargo': por_cargo
    })

@login_required
def rrhh(request):
    return render(request, 'rrhh/rrhh.html')

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
        documento = request.POST['documento']

        # VALIDAR DUPLICADO
        existe = Empleado.objects.filter(documento=documento).exclude(id=id).exists()

        if existe:
            return render(request, '/rrhh/detalle_empleado.html', {
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
        empleado.fecha_finalizacion = request.POST['fecha_finalizacion']
        empleado.tipo_contrato = request.POST['tipo_contrato']
        empleado.salario = request.POST['salario']
        empleado.jornada = request.POST['jornada']
        empleado.jefe = request.POST['jefe']

        # CONTACTO EMERGENCIA
        empleado.contacto_emergencia = request.POST.get('contacto_emergencia')
        empleado.telefono_emergencia = request.POST.get('telefono_emergencia')
        empleado.parentesco_emergencia = request.POST.get('parentesco_emergencia')

        # SEGURIDAD SOCIAL
        empleado.eps = request.POST.get('eps')
        empleado.arl = request.POST.get('arl')
        empleado.afp = request.POST.get('afp')
        empleado.cesantias = request.POST.get('cesantias')

        # OBSERVACIONES
        empleado.observaciones = request.POST.get('observaciones')

        empleado.save()

        # Actualizar o crear SaludEmpleado
        if salud:
            salud.grupo_sanguineo = request.POST.get('salud_grupo_sanguineo', '')
            salud.eps = request.POST.get('salud_eps', '')
            salud.pension = request.POST.get('salud_pension', '')
            salud.arl = request.POST.get('salud_arl', '')
            salud.alergias = request.POST.get('salud_alergias', '')
            salud.contacto_emergencia = request.POST.get('salud_contacto_emergencia', '')
            salud.telefono_emergencia = request.POST.get('salud_telefono_emergencia', '')
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

    return render(request, 'rrhh/detalle_empleado.html', {
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

    return render(request, 'rrhh/agregar_dotacion.html', {'empleado': empleado})

@login_required
def crear_empleado(request):
    if request.method == 'POST':
        try:
            empleado = Empleado.objects.create(
                nombre_completo=request.POST['nombre_completo'],
                documento=request.POST['documento'],
                ciudad_expedicion=request.POST.get('ciudad_expedicion', ''),
                fecha_nacimiento=request.POST['fecha_nacimiento'],
                nacionalidad=request.POST['nacionalidad'],
                direccion=request.POST['direccion'],
                ciudad_residencia=request.POST.get('ciudad_residencia', ''),
                telefono=request.POST['telefono'],
                correo=request.POST['correo'],
                cargo=request.POST['cargo'],
                area=request.POST['area'],
                nivel_academico=request.POST['nivel_academico'],
                profesion=request.POST.get('profesion', ''),
                habilidades=request.POST.get('habilidades', ''),
                idiomas=request.POST['idiomas'],
                fecha_ingreso=request.POST['fecha_ingreso'],
                fecha_finalizacion=request.POST['fecha_finalizacion'],
                tipo_contrato=request.POST['tipo_contrato'],
                salario=request.POST['salario'],
                jornada=request.POST['jornada'],
                jefe=request.POST['jefe']
            )

            SaludEmpleado.objects.create(
                empleado=empleado,
                grupo_sanguineo=request.POST['grupo_sanguineo'],
                eps=request.POST['eps'],
                pension=request.POST['pension'],
                cesantias=request.POST['cesantias'],
                arl=request.POST['arl'],
                alergias=request.POST.get('alergias', ''),
                contacto_emergencia=request.POST['contacto_emergencia'],
                telefono_emergencia=request.POST['telefono_emergencia']
            )

            return redirect('rrhh/empleados/')

        except IntegrityError:
            return render(request, 'crear_empleado.html', {
                'error': '⚠️ Ya existe un empleado con ese documento'
            })

    return render(request, 'rrhh/crear_empleado.html')

@login_required
def eliminar_empleado(request, id):
    empleado = get_object_or_404(Empleado, id=id)

    if request.method == 'POST':
        empleado.delete()
        return redirect('rrhh/empleados/')

    return redirect('rrhh/empleados/')

@login_required
def certificacion_laboral(request, id):

    empleado = Empleado.objects.get(id=id)

    contenido = f"""
    CERTIFICACIÓN LABORAL

    COINTECA S.A.S certifica que:

    {empleado.nombre_completo}

    identificado con documento No. {empleado.documento}

    trabaja con nosotros en el cargo de:

    {empleado.cargo}

    desde la fecha:

    {empleado.fecha_ingreso}

    con salario de:

    ${empleado.salario}
    """

    return HttpResponse(contenido, content_type='text/plain')

@login_required
def certificacion_laboral(request, id):

    empleado = get_object_or_404(Empleado, id=id)

    # RUTA PLANTILLA
    ruta_plantilla = os.path.join(
        settings.BASE_DIR,
        "core",
        "templates",
        "rrhh",
        "contratos",
        "certificacion_laboral.docx"
    )

    # ABRIR WORD
    doc = DocxTemplate(ruta_plantilla)

    # VARIABLES
    contexto = {
        "empleado": {
            "nombre_completo": empleado.nombre_completo.upper(),
            "documento": empleado.documento,
            "cargo": empleado.cargo.upper(),
            "salario": empleado.salario,
            "fecha_ingreso": empleado.fecha_ingreso.strftime("%d/%m/%Y"),
            "ciudad_expedicion": empleado.ciudad_expedicion.upper(),
        },
        "fecha_actual": date.today().strftime("%d/%m/%Y")
    }

    # REEMPLAZAR VARIABLES
    doc.render(contexto)

    # NOMBRE ARCHIVO
    ruta_salida = os.path.join(
        settings.MEDIA_ROOT,
        f"certificacion_{empleado.nombre_completo}.docx"
    )

    # GUARDAR
    doc.save(ruta_salida)

    # DESCARGAR
    return FileResponse(
        open(ruta_salida, "rb"),
        as_attachment=True,
        filename=f"certificacion_{empleado.nombre_completo}.docx"
    )

@login_required
def asignar_equipo(request, id):

    empleado = Empleado.objects.get(id=id)

    equipos = InventarioEquipo.objects.filter(
        estado='Disponible'
    )

    if request.method == 'POST':

        equipo = InventarioEquipo.objects.get(
            id=request.POST['equipo_inventario']
        )

        AsignacionEquipo.objects.create(
            empleado=empleado,
            equipo_inventario=equipo,
            fecha_entrega=request.POST['fecha_entrega'],
            observaciones=request.POST['observaciones']
        )

        # CAMBIAR ESTADO
        equipo.estado = 'Asignado'
        equipo.save()

        return redirect(f'/rrhh/empleados/{id}/')

    return render(request, 'rrhh/asignar_equipo.html', {
        'empleado': empleado,
        'equipos': equipos
    })
    

@login_required
def eliminar_equipo(request, id):

    equipo = AsignacionEquipo.objects.get(id=id)

    empleado_id = equipo.empleado.id

    equipo.delete()

    return redirect(f'/rrhh/empleados/{empleado_id}/')

@login_required
def editar_equipo(request, id):

    equipo = AsignacionEquipo.objects.get(id=id)

    empleado = equipo.empleado

    if request.method == 'POST':

        existe_serial = AsignacionEquipo.objects.filter(
            serial=request.POST['serial']
        ).exclude(id=id).exists()

        if existe_serial:

            return render(request, 'editar_equipo.html', {
                'empleado': empleado,
                'equipo': equipo,
                'error': '⚠️ Este serial ya está asignado a otro empleado'
            })

        equipo.equipo = request.POST['equipo']
        equipo.referencia = request.POST['referencia']
        equipo.serial = request.POST['serial']
        equipo.fecha_entrega = request.POST['fecha_entrega']
        equipo.observaciones = request.POST['observaciones']

        equipo.save()

        return redirect(f'/rrhh/empleados/{empleado.id}/')

    return render(request, 'editar_equipo.html', {
        'empleado': empleado,
        'equipo': equipo
    })

@login_required
def acta_entrega_equipos(request, id):

    empleado = get_object_or_404(Empleado, id=id)
    equipos = AsignacionEquipo.objects.filter(empleado=empleado)

    ruta_plantilla = os.path.join(
        settings.BASE_DIR,
        "core",
        "templates",
        "rrhh",
        "contratos",
        "acta_entrega.docx"
    )

    doc = DocxTemplate(ruta_plantilla)

    contexto = {
        "empleado": {
            "nombre_completo": empleado.nombre_completo.upper(),
            "documento": empleado.documento,
            "cargo": empleado.cargo.upper(),
        },

        "equipos": equipos,

        "fecha_actual": date.today().strftime("%d/%m/%Y"),
    }

    doc.render(contexto)

    ruta_salida = os.path.join(
        settings.MEDIA_ROOT,
        f"acta_entrega_{empleado.nombre_completo}.docx"
    )

    doc.save(ruta_salida)

    return FileResponse(
        open(ruta_salida, "rb"),
        as_attachment=True,
        filename=f"acta_entrega_{empleado.nombre_completo}.docx"
    )

@login_required
def inventario_equipos(request):

    equipos = InventarioEquipo.objects.all()

    # ACTUALIZAR ESTADO AUTOMÁTICAMENTE
    for e in equipos:

        asignado = AsignacionEquipo.objects.filter(
            equipo_inventario=e
        ).exists()

        if asignado:
            e.estado = 'Asignado'
        else:
            e.estado = 'Disponible'

        e.save()

    return render(request, 'rrhh/inventario_equipos.html', {
        'equipos': equipos
    })

@login_required
def crear_equipo_inventario(request):

    if request.method == 'POST':

        InventarioEquipo.objects.create(

            equipo=request.POST['equipo'],
            referencia=request.POST['referencia'],
            serial=request.POST['serial'],
            fecha_compra=request.POST['fecha_compra'],
            estado=request.POST['estado'],
            observaciones=request.POST['observaciones']

        )

        return redirect('inventario_equipos')

    return render(request, 'rrhh/crear_equipo_inventario.html')

@login_required
def editar_equipo_inventario(request, id):

    equipo = InventarioEquipo.objects.get(id=id)

    if request.method == 'POST':

        equipo.equipo = request.POST['equipo']
        equipo.referencia = request.POST['referencia']
        equipo.serial = request.POST['serial']
        equipo.marca = request.POST['marca']
        equipo.estado = request.POST['estado']
        equipo.fecha_compra = request.POST['fecha_compra']
        equipo.observaciones = request.POST['observaciones']

        equipo.save()

        return redirect('inventario_equipos')

    contexto = {
        'equipo': equipo
    }

    return render(
        request,
        'rrhh/editar_equipo_inventario.html',
        contexto
    )

@login_required
def eliminar_equipo_inventario(request, id):

    equipo = InventarioEquipo.objects.get(id=id)

    equipo.delete()

    return redirect('inventario_equipos')

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

    return render(request, 'rrhh/subir_documento.html', {
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

@login_required
def contrato_empleado(request, id):

    empleado = Empleado.objects.get(id=id)
    context = build_contract_context(empleado)

    return render(
        request,
        'rrhh/contratos/contrato_modular.html',
        context
    )

@login_required
def generar_contrato(request, id):

    empleado = get_object_or_404(Empleado, id=id)

    ruta_plantilla = os.path.join(
        settings.BASE_DIR,
        "core",
        "templates",
        "rrhh",
        "contratos",
        "test.docx"
    )

    # ABRIR PLANTILLA
    doc = DocxTemplate(ruta_plantilla)

    # VARIABLES
    contexto = {
        "empleado": {
            "nombre_completo": empleado.nombre_completo.upper(),
            "documento": empleado.documento,
            "direccion": empleado.direccion.upper(),
            "telefono": empleado.telefono,
            "cargo": empleado.cargo.upper(),
            "salario": empleado.salario,
            "fecha_ingreso": empleado.fecha_ingreso.strftime("%d/%m/%Y"),
            "fecha_finalizacion": empleado.fecha_finalizacion.strftime("%d/%m/%Y") if empleado.fecha_finalizacion else None,
            "tipo_contrato": empleado.tipo_contrato.upper(),
            "jornada": empleado.jornada.upper(),
            "ciudad_expedicion": empleado.ciudad_expedicion.upper(),
            "nacionalidad": empleado.nacionalidad.upper(),
            "ciudad_residencia": empleado.ciudad_residencia.upper(),
            "correo": empleado.correo.upper(),

        }
    }

    # REEMPLAZAR VARIABLES
    doc.render(contexto)

    # GUARDAR NUEVO WORD
    ruta_salida = os.path.join(
        settings.MEDIA_ROOT,
        f"contrato_{empleado.nombre_completo}.docx"
    )

    doc.save(ruta_salida)

    # DESCARGAR
    return FileResponse(
        open(ruta_salida, "rb"),
        as_attachment=True,
        filename=f"contrato_{empleado.nombre_completo}.docx"
    )

@login_required
def permiso_laboral(request, id):

    empleado = get_object_or_404(Empleado, id=id)

    return render(request, 'rrhh/permisos/index.html', {
        'empleado': empleado
    })

