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
    SaludEmpleado
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

    return render(request, 'empleados.html', {
        'empleados': lista,
        'query': query,
        'total': total,
        'promedio_salario': promedio_salario,
        'por_cargo': por_cargo
    })

@login_required
def rrhh(request):
    return render(request, 'rrhh.html')

@login_required
def detalle_empleado(request, id):
    empleado = Empleado.objects.get(id=id)

    salud = None
    try:
        salud = empleado.saludempleado
    except:
        pass

    dotaciones = DotacionEmpleado.objects.filter(empleado=empleado)

    editando = request.GET.get('edit')

    if request.method == 'POST':
        documento = request.POST['documento']

        # VALIDAR DUPLICADO
        existe = Empleado.objects.filter(documento=documento).exclude(id=id).exists()

        if existe:
            return render(request, 'detalle_empleado.html', {
                'empleado': empleado,
                'salud': salud,
                'dotaciones': dotaciones,
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

        empleado.save()

        messages.success(request, '✅ Empleado actualizado correctamente')

        return redirect(f'/rrhh/empleados/{id}/')

    # ✅ ESTE TE FALTABA (GET)
    return render(request, 'detalle_empleado.html', {
        'empleado': empleado,
        'salud': salud,
        'dotaciones': dotaciones,
        'editando': editando
    })

@login_required
def agregar_dotacion(request, id):
    empleado = Empleado.objects.get(id=id)

    if request.method == 'POST':
        elemento = request.POST['elemento']
        descripcion = request.POST['descripcion']
        fecha = request.POST['fecha']

        DotacionEmpleado.objects.create(
            empleado=empleado,
            elemento=elemento,
            descripcion=descripcion,
            fecha_entrega=fecha
        )

        return redirect(f'/rrhh/empleados/{id}/')

    return render(request, 'agregar_dotacion.html', {'empleado': empleado})

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

            return redirect('/rrhh/empleados/')

        except IntegrityError:
            return render(request, 'crear_empleado.html', {
                'error': '⚠️ Ya existe un empleado con ese documento'
            })

    return render(request, 'crear_empleado.html')

@login_required
def eliminar_empleado(request, id):
    empleado = get_object_or_404(Empleado, id=id)

    if request.method == 'POST':
        empleado.delete()
        return redirect('/rrhh/empleados/')

    return redirect('/rrhh/empleados/')

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