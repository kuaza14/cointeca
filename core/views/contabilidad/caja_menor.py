from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.conf import settings
import os
import openpyxl
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from decimal import Decimal

from core.models import (
    CajaMenor,
    MovimientoCajaMenor
)


# =========================================================================
# 💵 VISTAS DE CAJA MENOR (CONTABILIDAD & GESTIÓN DOCUMENTAL RRHH-FOR-12)
# =========================================================================

@login_required 
def caja_menor(request):
    """
    Lista todos los trámites de caja menor con métricas y resumen financiero.
    """
    cajas = CajaMenor.objects.all().order_by('-fecha_tramite', '-id')

    total_inicial = sum([c.valor_inicial for c in cajas]) if cajas else 0
    total_gastado = sum([c.total_gastado for c in cajas]) if cajas else 0
    total_restante = sum([c.valor_restante for c in cajas]) if cajas else 0

    return render(request, 'contabilidad/caja_menor.html', {
        'cajas': cajas,
        'total_inicial': total_inicial,
        'total_gastado': total_gastado,
        'total_restante': total_restante,
    })


@login_required
def crear_caja(request):
    """
    Crea un nuevo trámite de caja menor con fondo fijo asignado.
    """
    if request.method == 'POST':
        fecha_tramite = request.POST.get('fecha_tramite')
        fecha_cierre = request.POST.get('fecha_cierre') or None
        valor_raw = request.POST.get('valor_inicial', '0').replace('$', '').replace('.', '').replace(',', '').strip()
        valor_inicial = Decimal(valor_raw) if valor_raw else Decimal('0')

        caja = CajaMenor.objects.create(
            fecha_tramite=fecha_tramite,
            fecha_cierre=fecha_cierre,
            valor_inicial=valor_inicial,
            total_gastado=Decimal('0'),
            valor_restante=valor_inicial
        )
        return redirect('detalle_caja', id=caja.id)

    return render(request, 'contabilidad/crear_caja.html')


@login_required
def editar_caja(request, id):
    """
    Modifica las fechas y el valor inicial de una caja menor.
    """
    caja = get_object_or_404(CajaMenor, id=id)

    if request.method == 'POST':
        caja.fecha_tramite = request.POST.get('fecha_tramite')
        caja.fecha_cierre = request.POST.get('fecha_cierre') or None
        valor_raw = request.POST.get('valor_inicial', '0').replace('$', '').replace('.', '').replace(',', '').strip()
        caja.valor_inicial = Decimal(valor_raw) if valor_raw else Decimal('0')
        caja.save()
        caja.calcular_totales()
        return redirect('detalle_caja', id=caja.id)

    return render(request, 'contabilidad/editar_caja.html', {'caja': caja})


@login_required
def eliminar_caja(request, id):
    """
    Elimina un trámite de caja menor completo y sus movimientos.
    """
    caja = get_object_or_404(CajaMenor, id=id)
    caja.delete()
    return redirect('caja_menor')


@login_required
def detalle_caja(request, id):
    """
    Muestra el detalle del trámite de caja menor con sus movimientos.
    """
    caja = get_object_or_404(CajaMenor, id=id)
    movimientos = caja.movimientocajamenor_set.all().order_by('fecha', 'id')

    # Porcentaje consumido
    porcentaje_consumido = 0
    if caja.valor_inicial > 0:
        porcentaje_consumido = round((caja.total_gastado / caja.valor_inicial) * 100, 1)

    return render(request, 'contabilidad/detalle_caja.html', {
        'caja': caja,
        'movimientos': movimientos,
        'porcentaje_consumido': porcentaje_consumido,
    })


@login_required
def agregar_movimiento(request, id):
    """
    Registra un gasto / factura a la caja menor.
    """
    caja = get_object_or_404(CajaMenor, id=id)

    if request.method == 'POST':
        valor_raw = request.POST.get('valor', '0').replace('$', '').replace('.', '').replace(',', '').strip()
        valor = Decimal(valor_raw) if valor_raw else Decimal('0')

        MovimientoCajaMenor.objects.create(
            caja=caja,
            fecha=request.POST.get('fecha'),
            numero_factura=request.POST.get('numero_factura', '').strip(),
            nit=request.POST.get('nit', '').strip(),
            pagado_a=request.POST.get('pagado_a', '').strip(),
            concepto=request.POST.get('concepto', '').strip(),
            valor=valor
        )
        return redirect('detalle_caja', id=caja.id)

    return render(request, 'contabilidad/agregar_movimiento.html', {'caja': caja})


@login_required
def editar_movimiento(request, id):
    """
    Edita un movimiento existente y recalcula los totales.
    """
    movimiento = get_object_or_404(MovimientoCajaMenor, id=id)

    if request.method == 'POST':
        valor_raw = request.POST.get('valor', '0').replace('$', '').replace('.', '').replace(',', '').strip()
        valor = Decimal(valor_raw) if valor_raw else Decimal('0')

        movimiento.fecha = request.POST.get('fecha')
        movimiento.numero_factura = request.POST.get('numero_factura', '').strip()
        movimiento.nit = request.POST.get('nit', '').strip()
        movimiento.pagado_a = request.POST.get('pagado_a', '').strip()
        movimiento.concepto = request.POST.get('concepto', '').strip()
        movimiento.valor = valor
        movimiento.save()

        return redirect('detalle_caja', id=movimiento.caja.id)

    return render(request, 'contabilidad/editar_movimiento.html', {'m': movimiento})


@login_required
def eliminar_movimiento(request, id):
    """
    Elimina un movimiento de gasto y actualiza el saldo de la caja.
    """
    movimiento = get_object_or_404(MovimientoCajaMenor, id=id)
    caja = movimiento.caja
    caja_id = caja.id

    movimiento.delete()
    caja.calcular_totales()

    return redirect('detalle_caja', id=caja_id)


# =========================================================================
# 📥 EXPORTACIÓN A EXCEL OFICIAL: FORMATO RRHH-FOR-12
# =========================================================================

@login_required
def exportar_caja_menor_excel(request, id):
    """
    Genera y descarga el formato oficial institucional de Caja Menor (RRHH-FOR-12).
    Usa la plantilla base de Excel si existe o construye el libro estructurado idéntico.
    """
    caja = get_object_or_404(CajaMenor, id=id)
    movimientos = caja.movimientocajamenor_set.all().order_by('fecha', 'id')

    ruta_plantilla = os.path.join(settings.BASE_DIR, 'plantillas_excel', 'formato_caja_menor.xlsx')

    if os.path.exists(ruta_plantilla):
        wb = load_workbook(ruta_plantilla)
        ws = wb.active
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Hoja1"

    # Encabezado institucional
    ws['B8'] = "FECHA DE TRAMITE:"
    ws['D8'] = str(caja.fecha_tramite) if caja.fecha_tramite else ""
    ws['B9'] = "FECHA DE CIERRE"
    ws['D9'] = str(caja.fecha_cierre) if caja.fecha_cierre else ""

    ws['G8'] = "VALOR DE LA CAJA MENOR "
    ws['H8'] = float(caja.valor_inicial)

    # Llenado de filas de movimientos a partir de la fila 14
    fila_inicio = 14
    borde_fino = Border(
        left=Side(style='thin', color='D1D5DB'),
        right=Side(style='thin', color='D1D5DB'),
        top=Side(style='thin', color='D1D5DB'),
        bottom=Side(style='thin', color='D1D5DB')
    )

    for i, m in enumerate(movimientos):
        fila_actual = fila_inicio + i
        ws[f'B{fila_actual}'] = str(m.fecha)
        ws[f'C{fila_actual}'] = str(m.numero_factura)
        ws[f'D{fila_actual}'] = str(m.nit)
        ws[f'E{fila_actual}'] = str(m.pagado_a)
        ws[f'F{fila_actual}'] = str(m.concepto)
        ws[f'H{fila_actual}'] = float(m.valor)

        # Formato numérico en columna H
        ws[f'H{fila_actual}'].number_format = '$#,##0'

    # Fila final para la suma
    fila_fin = max(fila_inicio + len(movimientos) - 1, 56)
    ws['G9'] = "TOTAL DE CAJA MENOR "
    ws['H9'] = float(caja.total_gastado)
    ws['H9'].number_format = '$#,##0'

    ws['G10'] = "VALOR RESTANTE DE CAJA "
    ws['H10'] = float(caja.valor_restante)
    ws['H10'].number_format = '$#,##0'

    # Configurar respuesta HTTP para descarga directa
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    nombre_archivo = f"RRHH-FOR-12_Caja_Menor_{caja.fecha_tramite}.xlsx"
    response["Content-Disposition"] = f'attachment; filename="{nombre_archivo}"'

    wb.save(response)
    return response