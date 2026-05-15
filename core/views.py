from django.shortcuts import render, redirect
from django.db.models import Avg, Count, Sum
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .models import (
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
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from io import BytesIO
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.platypus.flowables import HRFlowable
from weasyprint import HTML
from django.template.loader import render_to_string
from django.conf import settings 
import os


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
        empleado.telefono = request.POST['telefono']
        empleado.correo = request.POST['correo']

        empleado.cargo = request.POST['cargo']
        empleado.area = request.POST['area']
        empleado.nivel_academico = request.POST['nivel_academico']
        empleado.profesion = request.POST['profesion']
        empleado.habilidades = request.POST['habilidades']
        empleado.idiomas = request.POST['idiomas']

        empleado.fecha_ingreso = request.POST['fecha_ingreso']
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
                telefono=request.POST['telefono'],
                correo=request.POST['correo'],
                cargo=request.POST['cargo'],
                area=request.POST['area'],
                nivel_academico=request.POST['nivel_academico'],
                profesion=request.POST.get('profesion', ''),
                habilidades=request.POST.get('habilidades', ''),
                idiomas=request.POST['idiomas'],
                fecha_ingreso=request.POST['fecha_ingreso'],
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

    empleado = Empleado.objects.get(id=id)

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=50,
        leftMargin=50,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    titulo_style = ParagraphStyle(
        'Titulo',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        fontSize=18,
        textColor=colors.HexColor("#003366"),
        spaceAfter=30
    )

    texto_style = ParagraphStyle(
        'Texto',
        parent=styles['BodyText'],
        alignment=TA_JUSTIFY,
        fontSize=12,
        leading=16
    )

    firma_style = ParagraphStyle(
        'Firma',
        parent=styles['BodyText'],
        fontSize=12,
        leading=20
    )

    elementos = []

    # LOGO
    logo = Image('static/img/logo-cointeca.png', width=100, height=60)

    encabezado_data = [
        [
            logo,
            "Tipo de documento: Formato",
            "Código: RRHH-FR-10"
        ],
        [
            "",
            "CERTIFICACIÓN LABORAL",
            "Versión: 2"
        ],
        [
            "",
            "",
            "Fecha: 02/03/2026"
        ],
        [
            "",
            "",
            "Página 1 de 1"
        ]
    ]

    tabla = Table(
    encabezado_data,
    colWidths=[110, 250, 130],
    rowHeights=[16, 22, 16, 16]
    )

    tabla.setStyle(TableStyle([

        ('GRID', (0,0), (-1,-1), 1, colors.black),

        # LOGO
        ('SPAN', (0,0), (0,3)),
        ('SPAN', (1,1), (1,3)),
        ('VALIGN', (1,1), (1,3), 'MIDDLE'),
        ('ALIGN', (1,1), (1,3), 'CENTER'),

        ('ALIGN', (1,0), (1,0), 'LEFT'),

        # TEXTO CENTRO 
        ('ALIGN', (1,0), (1,0), 'CENTER'),
        ('ALIGN', (1,1), (1,1), 'CENTER'),

        # DERECHA 
        ('VALIGN', (2,0), (2,3), 'MIDDLE'),

        # FUENTES 
        ('FONTNAME', (1,0), (1,0), 'Helvetica-Bold'),
        ('FONTNAME', (1,1), (1,1), 'Helvetica-Bold'),

        ('FONTSIZE', (1,0), (1,0), 8),
        ('FONTSIZE', (1,1), (1,1), 12),

        ('FONTSIZE', (2,0), (2,3), 8),

        # PADDING PEQUEÑO
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),

    ]))

    elementos.append(tabla)

    elementos.append(Spacer(1, 25))
    elementos.append(HRFlowable(
        width="100%",
        thickness=1,
        color=colors.black
    ))

    elementos.append(Spacer(1, 10))

    texto = f"""
    La suscrita <b>Mayra Alejandra Ocoró Possú</b>,
    identificada con cédula de ciudadanía No.
    <b>1.060.416.458</b> de Padilla Cauca,
    actuando en calidad de representante legal de
    <b>COMERCIALIZADORA DE INGENIERÍA &amp; TECNOLOGÍAS APLICADAS S.A.S COINTECA S.A.S</b>
    con NIT <b>900.768.648-3</b>.
    <br/><br/>"""
    
    elementos.append(Paragraph(texto, texto_style))

    certifica_style = ParagraphStyle(
        'Certifica',
        parent=styles['BodyText'],
        alignment=TA_CENTER,
        fontSize=14,
        leading=18,
        spaceBefore=15,
        spaceAfter=20
    )

    elementos.append(
        Paragraph("<b>CERTIFICA QUE</b>", certifica_style)
    )
    texto_empleado = f"""
    El señor(a) <b>{empleado.nombre_completo}</b>,
    identificado(a) con cédula de ciudadanía No.
    <b>{empleado.documento}</b>, de
    <b>{empleado.ciudad_expedicion}</b>,
    se encuentra vinculado laboralmente con nuestra empresa
    cumpliendo conforme a lo siguiente:
    """

    elementos.append(Paragraph(texto_empleado, texto_style))

    elementos.append(Spacer(1, 10))

    info = f"""
    • <b>Cargo:</b> {empleado.cargo}<br/>
    • <b>Tipo de contrato:</b> {empleado.tipo_contrato}<br/>
    • <b>Fecha de ingreso:</b> {empleado.fecha_ingreso}<br/>
    • <b>Salario:</b> ${empleado.salario} M/cte.<br/>
    """

    elementos.append(Paragraph(info, texto_style))

    elementos.append(Spacer(1, 30))

    texto_final = """
    <br/>
    Para constancia de lo anterior se firma la presente certificación laboral.
    """


    elementos.append(Paragraph(texto_final, texto_style))

    elementos.append(Spacer(1, 80))

    elementos.append(
        HRFlowable(
            width="40%", 
            hAlign = 'LEFT' 
        )
    )

    firma = """
    <b>Mayra Alejandra Ocoró Possú</b><br/>
    Representante Legal<br/>
    COINTECA S.A.S
    """

    elementos.append(Paragraph(firma, firma_style))
    footer = Paragraph(
        """
        <font color="white">
        cointecasas@hotmail.com &nbsp;&nbsp; - &nbsp;&nbsp;
        Tel. 3117121043 &nbsp;&nbsp; - &nbsp;&nbsp;
        www.cointecasas.com
        </font>
        """,
        ParagraphStyle(
            'footer',
            alignment=1,
            backColor=colors.HexColor("#1D4ED8"),
            textColor=colors.white,
            fontSize=10,
            leading=15,
            spaceBefore=30,
            spaceAfter=0,
            padding=10
        )
    )

    elementos.append(Spacer(1, 25))
    elementos.append(footer)

    # CREAR PDF
    doc.build(elementos)

    buffer.seek(0)

    return FileResponse(
        buffer,
        as_attachment=True,
        filename='certificacion_laboral.pdf'
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

    empleado = Empleado.objects.get(id=id)
    equipos = AsignacionEquipo.objects.filter(empleado=empleado)

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    texto_style = ParagraphStyle(
        'Texto',
        parent=styles['BodyText'],
        alignment=TA_JUSTIFY,
        fontSize=9,
        leading=14
    )

    elementos = []

    # === ENCABEZADO === (no lo tocamos)
    logo = Image('static/img/logo-cointeca.png', width=100, height=60)
    encabezado_data = [
        [logo, "Tipo de documento: Formato", "Código: RRHH-FR-11"],
        ["",   "ACTA ENTREGA DE EQUIPOS",    "Versión: 1"],
        ["",   "",                            "Fecha: 28/04/2026"],
        ["",   "",                            "Página 1 de 1"]
    ]
    tabla = Table(encabezado_data, colWidths=[110, 250, 130], rowHeights=[16, 22, 16, 16])
    tabla.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('SPAN', (0,0), (0,3)),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (0,0), 'CENTER'),
        ('ALIGN', (1,0), (1,0), 'LEFT'),
        ('ALIGN', (1,1), (1,1), 'CENTER'),
        ('FONTNAME', (1,1), (1,1), 'Helvetica-Bold'),
        ('FONTSIZE', (1,0), (1,0), 8),
        ('FONTSIZE', (1,1), (1,1), 12),
        ('FONTSIZE', (2,0), (2,3), 8),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    elementos.append(tabla)
    elementos.append(Spacer(1, 15))

    # === TEXTO PRINCIPAL ===
    texto = f"""
    <b>ENTRE LOS SUSCRITOS:</b>
    <br/><br/>
    COINTECA S.A.S., identificada con NIT 900.768.648, representada legalmente por 
    <b>[Nombre del Representante]</b>, en adelante el EMPLEADOR, y por la otra parte 
    <b>{empleado.nombre_completo}</b>, identificado(a) con C.C. <b>{empleado.documento}</b>, 
    en adelante el TRABAJADOR, han convenido de manera libre y voluntaria adicionar 
    al contrato de trabajo vigente las siguientes cláusulas:
    """
    elementos.append(Paragraph(texto, texto_style))
    elementos.append(Spacer(1, 12))

    # === CLAUSULA 1 ===
    clausula1 = """
    <b>1. CLÁUSULA PRIMERA: OBJETO Y ESPECIFICACIONES TÉCNICAS</b> El TRABAJADOR. 
    Recibe en calidad de herramienta de trabajo los siguientes equipos para el 
    desempeño exclusivo de sus funciones:
    """
    elementos.append(Paragraph(clausula1, texto_style))
    elementos.append(Spacer(1, 8))

    # === TABLA EQUIPOS (solo los asignados + filas vacías abajo) ===
    data = [['Elemento', 'Marca / Referencia', 'Serial / IMEI', 'Estado Inicial', 'Observaciones']]

    for e in equipos:
        data.append([e.equipo, e.marca if hasattr(e, 'marca') else '', e.serial, 'Bueno', e.observaciones or ''])

    # Filas vacías extra para escribir a mano
    for _ in range(1):
        data.append(['', '', '', '', ''])

    from reportlab.platypus import Paragraph as P

    # Convertir observaciones a Paragraph para que haga wrap
    data2 = [data[0]]  # encabezado
    for fila in data[1:]:
        data2.append([
            fila[0], fila[1], fila[2], fila[3],
            Paragraph(str(fila[4]), ParagraphStyle('obs', fontSize=7, leading=10))
        ])

    tabla_equipos = Table(data2, colWidths=[80, 100, 90, 70, 150])
    tabla_equipos.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.8, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#D9EAF7")),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWHEIGHT', (0,1), (-1,-1), 18),
        ('TOPPADDING', (0,0), (-1,0), 5),
        ('BOTTOMPADDING', (0,0), (-1,0), 5),
        ('WORDWRAP', (4,1), (4,-1), True),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    elementos.append(tabla_equipos)
    elementos.append(Spacer(1, 12))

    # === CLAUSULAS 2-5 ===
    clausulas = """
    <b>2. CLÁUSULA SEGUNDA: OBLIGACIONES Y USO DE LOS EQUIPOS</b>
    <br/>
    a) <b>Uso Exclusivo Laboral:</b> El TRABAJADOR manifiesta que recibe los equipos en perfecto 
    estado y se obliga a usarlos exclusivamente para los fines definidos por la empresa.
    <br/>
    b) <b>Prohibición de Uso Personal:</b> Se prohíbe el uso de los equipos para actividades 
    personales, así como prestarlos a familiares, amigos o terceros. Cualquier ilícito cometido 
    mediante estos equipos será responsabilidad exclusiva del trabajador.
    <br/>
    c) <b>Restitución:</b> El TRABAJADOR se obliga a devolver los equipos en el mismo estado en 
    que los recibió (salvo el deterioro natural) cuando el EMPLEADOR lo requiera o al finalizar 
    el contrato.
    <br/><br/>
    <b>3. CLÁUSULA TERCERA: AUTORIZACIÓN EXPRESA DE DESCUENTO.</b> En cumplimiento del Art. 59 
    del CST, el TRABAJADOR autoriza de manera expresa, permanente e irrevocable a COINTECA S.A.S. 
    para descontar de sus salarios, prestaciones sociales (cesantías, intereses, primas), 
    vacaciones, bonificaciones e indemnizaciones, el valor comercial de los equipos en caso de:
    <br/>
    • No devolución de los elementos al término del contrato.
    <br/>
    • Pérdida, hurto o daño total/parcial derivado de culpa, negligencia o mal uso.
    <br/>
    • Daños por manipulación de software no autorizado o retiro de sellos de seguridad.
    <br/><br/>
    <b>4. CLÁUSULA CUARTA: RÉGIMEN DISCIPLINARIO (FALTA GRAVE).</b> El TRABAJADOR acepta que 
    el incumplimiento de cualquiera de las obligaciones aquí pactadas constituye una FALTA GRAVE 
    a sus deberes laborales. En consecuencia, se considera Justa Causa para la terminación 
    unilateral del contrato de trabajo, según el Art. 62 del Código Sustantivo del Trabajo, 
    numeral 6.
    <br/><br/>
    <b>5. CLÁUSULA QUINTA: TRATAMIENTO DE DATOS Y MONITOREO.</b> El TRABAJADOR reconoce que, 
    al ser herramientas de propiedad de la empresa, COINTECA S.A.S. se reserva el derecho de 
    realizar auditorías, monitoreo de tráfico de datos y revisión de los equipos para garantizar 
    la seguridad de la información corporativa, conforme a la Ley 1581 de 2012.
    <br/><br/>
    En constancia de lo anterior, se firma en la ciudad de Santiago de Cali, a los ____ días 
    del mes de _______________ de 2026.
    """
    elementos.append(Paragraph(clausulas, texto_style))
    elementos.append(Spacer(1, 25))

    # === FIRMAS ===
    firmas = Table([
        ["__________________________________", "__________________________________"],
        ["EL EMPLEADOR (COINTECA S.A.S.)",    "EL TRABAJADOR"],
        ["NIT: 900.768.648",                   f"C.C. No: {empleado.documento}"]
    ], colWidths=[260, 260])

    firmas.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    elementos.append(firmas)
    elementos.append(Spacer(1, 20))

    # === FOOTER ===
    footer = Paragraph(
        '<font color="white">cointecasas@hotmail.com &nbsp;&nbsp;-&nbsp;&nbsp; Tel. 3117121043 &nbsp;&nbsp;-&nbsp;&nbsp; www.cointecasas.com</font>',
        ParagraphStyle('footer', alignment=1, backColor=colors.HexColor("#1D4ED8"), textColor=colors.white, fontSize=9, leading=15)
    )
    elementos.append(footer)

    doc.build(elementos)
    buffer.seek(0)

    return FileResponse(buffer, as_attachment=True, filename='acta_equipos.pdf')

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

    contrato = {
        'numero': f'CT-2026-{empleado.id}',
        'duracion': '1 año'
    }

    return render(
        request,
        'rrhh/contratos/contrato_base.html',
        {
            'empleado': empleado,
            'contrato': contrato
        }
    )

@login_required
def generar_contrato_pdf(request, id):

    empleado = Empleado.objects.get(id=id)

    contrato = {
        'numero': f'CT-2026-{empleado.id}',
        'duracion': '1 año'
    }

    logo_path = os.path.join(
        settings.BASE_DIR,
        'static',
        'img',
        'logo-cointeca.png'
    )

    html_string = render_to_string(
        'rrhh/contratos/contrato_base.html',
        {
            'empleado': empleado,
            'contrato': contrato,
            'logo_path': logo_path
        }
    )

    response = HttpResponse(
        content_type='application/pdf'
    )

    response['Content-Disposition'] = (
        f'inline; filename="contrato_{empleado.id}.pdf"'
    )

    HTML(
        string=html_string,
        base_url=request.build_absolute_uri('/')
    ).write_pdf(response)


    return response