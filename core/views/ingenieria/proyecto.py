import io
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from decimal import Decimal
from django.db.models import Sum
from django.utils import timezone
from core.models import (
    Proyecto,
    Apoyo,
    Material,
    ApoyoMaterial,
    ApoyoLuminaria,
    Empleado,
    Inventario,
    EntradaMaterialProyecto,
    DetalleEntradaMaterial,
)
from django.db import transaction
from django.contrib.auth.decorators import login_required




@login_required
def ingenieria_inicio(request):
    return render(
        request,
        "ingenieria/ingenieria_inicio.html"
    )

@login_required
def lista_proyectos(request):
    proyectos = Proyecto.objects.all().order_by("-id")
    return render(
        request,
        "ingenieria/proyecto/lista.html",
        {
            "proyectos": proyectos
        }
    )

@login_required
def crear_proyecto(request):
    if request.method == "POST":
        Proyecto.objects.create(
            numero_emcali=request.POST.get("numero_emcali"),
            tipo=request.POST.get("tipo")
        )
        return redirect("lista_proyectos")
    return redirect("lista_proyectos")

@login_required
def detalle_proyecto(request, id):
    proyecto = get_object_or_404(Proyecto, id=id)

    apoyos = (
        Apoyo.objects
        .filter(proyecto=proyecto)
        .select_related("quien_ejecuta")
        .prefetch_related("luminarias")   
        .order_by("numero_apoyo", "id")
    )

    # 1. Obtener todos los materiales únicos asignados a los apoyos de este proyecto
    apoyo_materiales = ApoyoMaterial.objects.filter(
        apoyo__proyecto=proyecto
    ).select_related("material")

    materiales_ids = apoyo_materiales.values_list('material_id', flat=True).distinct()
    materiales_columnas = list(Material.objects.filter(id__in=materiales_ids).order_by("descripcion"))

    cantidades_map = {}
    for am in apoyo_materiales:
        cantidades_map[(am.apoyo_id, am.material_id)] = am.cantidad_requerida

    # 3. Construir filas de la matriz estilo Excel (Filas = Apoyos/Nodos, Columnas = Materiales)
    filas_matriz = []
    totales_por_columna = {mat.id: Decimal("0") for mat in materiales_columnas}

    for ap in apoyos:
        celdas = []
        for mat in materiales_columnas:
            cant = cantidades_map.get((ap.id, mat.id), Decimal("0"))
            celdas.append({
                "material": mat,
                "cantidad": cant,
            })
            totales_por_columna[mat.id] += cant

        filas_matriz.append({
            "apoyo": ap,
            "celdas": celdas,
        })

    # 4. Fila de Totales Generales
    fila_totales = []
    for mat in materiales_columnas:
        fila_totales.append({
            "material": mat,
            "total": totales_por_columna.get(mat.id, Decimal("0")),
        })

    return render(
        request,
        "ingenieria/proyecto/detalle_proyecto.html",
        {
            "proyecto": proyecto,
            "apoyos": apoyos,
            "materiales_columnas": materiales_columnas,
            "filas_matriz": filas_matriz,
            "fila_totales": fila_totales,
        }
    )

@login_required
def crear_apoyo(request, proyecto_id):
    proyecto = get_object_or_404(
        Proyecto,
        id=proyecto_id
    )

    if request.method == "POST":
        numero_apoyo_val = request.POST.get("numero_apoyo")
        numero_apoyo = int(numero_apoyo_val) if numero_apoyo_val and numero_apoyo_val.isdigit() else None

        apoyo = Apoyo.objects.create(
            proyecto=proyecto,
            numero_apoyo=numero_apoyo,
            nodo=request.POST.get("nodo", "").strip(),
            estado="Pendiente"
        )

        potencias = request.POST.getlist("potencia[]")
        codigos = request.POST.getlist("codigo_luminaria[]")

        for potencia, codigo in zip(potencias, codigos):

            if potencia.strip() or codigo.strip():

                ApoyoLuminaria.objects.create(
                    apoyo=apoyo,
                    potencia=potencia.strip(),
                    codigo=codigo.strip()
                )

    return redirect(
        "detalle_proyecto",
        id=proyecto.id        
    )


@login_required
@transaction.atomic
def detalle_apoyo(request, apoyo_id):
    apoyo = get_object_or_404(Apoyo, id=apoyo_id)

    materiales_asociados = ApoyoMaterial.objects.filter(
        apoyo=apoyo
    ).select_related("material")

    materiales_catalogo = Material.objects.select_related("inventario").order_by("descripcion")

    empleados = Empleado.objects.filter(
        estado="activo"
    ).order_by("nombre_completo")

    if request.method == "POST":
        accion = request.POST.get("accion")

        # 1. DESPACHAR DIRECTO DESDE BODEGA CENTRAL
        if accion == "despachar_bodega":
            material_id = request.POST.get("material_id")
            cantidad_str = request.POST.get("cantidad", "0")

            if material_id:
                try:
                    cant = Decimal(cantidad_str.strip())
                    if cant > 0:
                        material = get_object_or_404(Material, id=material_id)
                        inventario, _ = Inventario.objects.get_or_create(material=material)

                        # Descontar del inventario general de bodega
                        inventario.cantidad = max(Decimal("0"), inventario.cantidad - cant)
                        inventario.save()

                        # Registrar la entrada al proyecto desde bodega
                        fecha_hoy = timezone.now().date()
                        nodo_label = apoyo.nodo or str(apoyo.numero_apoyo or "Poste")
                        entrada = EntradaMaterialProyecto.objects.create(
                            proyecto=apoyo.proyecto,
                            fecha=fecha_hoy,
                            proveedor="Bodega Central (Despacho)",
                            numero_remision=f"DESP-BOD-NODO-{nodo_label}",
                            recibido_por=apoyo.quien_ejecuta.nombre_completo if apoyo.quien_ejecuta else "Técnico en Terreno",
                            observaciones=f"Material despachado desde bodega central para el Nodo {nodo_label}"
                        )
                        DetalleEntradaMaterial.objects.create(
                            entrada=entrada,
                            material=material,
                            cantidad=cant
                        )

                        # Asignar / sumar el material a este apoyo en la obra
                        apoyo_mat, created = ApoyoMaterial.objects.get_or_create(
                            apoyo=apoyo,
                            material=material,
                            defaults={"cantidad_requerida": cant}
                        )
                        if not created:
                            apoyo_mat.cantidad_requerida += cant
                            apoyo_mat.save()

                except (ValueError, TypeError):
                    pass

            return redirect("detalle_apoyo", apoyo_id=apoyo.id)

        # 2. EDITAR MATERIAL ASIGNADO
        if accion == "editar_material":
            item_id = request.POST.get("item_id")
            cantidad = request.POST.get("cantidad")

            try:
                cant_decimal = Decimal(cantidad)

                if item_id and cant_decimal > 0:
                    apoyo_mat = ApoyoMaterial.objects.filter(
                        id=item_id,
                        apoyo=apoyo
                    ).first()

                    if apoyo_mat:
                        diferencia = cant_decimal - apoyo_mat.cantidad_requerida
                        inventario, _ = Inventario.objects.get_or_create(material=apoyo_mat.material)
                        inventario.cantidad = max(Decimal("0"), inventario.cantidad - diferencia)
                        inventario.save()

                        apoyo_mat.cantidad_requerida = cant_decimal
                        apoyo_mat.save()

            except (ValueError, TypeError, ArithmeticError):
                pass

            return redirect("detalle_apoyo", apoyo_id=apoyo.id)

        # 3. ELIMINAR MATERIAL DEL APOYO (DEVUELVE A BODEGA)
        if accion == "eliminar_material":
            item_id = request.POST.get("item_id")

            if item_id:
                apoyo_mat = ApoyoMaterial.objects.filter(
                    id=item_id,
                    apoyo=apoyo
                ).first()

                if apoyo_mat:
                    inventario, _ = Inventario.objects.get_or_create(material=apoyo_mat.material)
                    inventario.cantidad += apoyo_mat.cantidad_requerida
                    inventario.save()
                    apoyo_mat.delete()

            return redirect("detalle_apoyo", apoyo_id=apoyo.id)

        # 4. GUARDAR DATOS DEL APOYO
        apoyo.nodo = request.POST.get("nodo", "").strip()

        numero_apoyo = request.POST.get("numero_apoyo")
        apoyo.numero_apoyo = (
            int(numero_apoyo)
            if numero_apoyo and numero_apoyo.isdigit()
            else None
        )

        apoyo.estado = request.POST.get(
            "estado",
            apoyo.estado
        )

        empleado_id = request.POST.get("quien_ejecuta")

        if empleado_id and str(empleado_id).strip().isdigit():
            apoyo.quien_ejecuta_id = int(str(empleado_id).strip())
        else:
            apoyo.quien_ejecuta = None

        apoyo.observacion = request.POST.get(
            "observacion",
            ""
        ).strip()
        apoyo.save()

        # 5. GUARDAR Y DESCONTAR NUEVOS MATERIALES ASIGNADOS AL APOYO
        materiales_ids = request.POST.getlist("material_id[]")
        cantidades = request.POST.getlist("cantidad[]")

        for material_id, cantidad in zip(materiales_ids, cantidades):
            if not material_id or not cantidad:
                continue

            try:
                cant_nueva = Decimal(cantidad)
                if cant_nueva <= 0:
                    continue

                inventario, _ = Inventario.objects.get_or_create(material_id=material_id)
                apoyo_mat = ApoyoMaterial.objects.filter(
                    apoyo=apoyo,
                    material_id=material_id
                ).first()

                if apoyo_mat:
                    # Ajustar diferencia
                    diferencia = cant_nueva - apoyo_mat.cantidad_requerida
                    inventario.cantidad = max(Decimal("0"), inventario.cantidad - diferencia)
                    inventario.save()

                    apoyo_mat.cantidad_requerida = cant_nueva
                    apoyo_mat.save()
                else:
                    # Descontar de Bodega
                    inventario.cantidad = max(Decimal("0"), inventario.cantidad - cant_nueva)
                    inventario.save()

                    # Asignar al apoyo
                    ApoyoMaterial.objects.create(
                        apoyo=apoyo,
                        material_id=material_id,
                        cantidad_requerida=cant_nueva
                    )

            except (ValueError, TypeError, ArithmeticError):
                continue

        # DECIDIR A DÓNDE VOLVER
        if "guardar_y_volver" in request.POST:
            return redirect(
                "detalle_proyecto",
                id=apoyo.proyecto.id
            )

        return redirect(
            "detalle_apoyo",
            apoyo_id=apoyo.id
        )

    return render(
        request,
        "ingenieria/apoyos/detalle_apoyo.html",
        {
            "apoyo": apoyo,
            "materiales_asociados": materiales_asociados,
            "materiales_catalogo": materiales_catalogo,
            "empleados": empleados,
        }
    )

@login_required
@transaction.atomic
def eliminar_apoyo(request, apoyo_id):
    apoyo = get_object_or_404(
        Apoyo,
        id=apoyo_id
    )

    proyecto_id = apoyo.proyecto.id

    if request.method == "POST":
        # Devolver materiales asignados a la bodega central
        for am in apoyo.materiales.all():
            inventario, _ = Inventario.objects.get_or_create(material=am.material)
            inventario.cantidad += am.cantidad_requerida
            inventario.save()

        apoyo.delete()

    return redirect(
        "detalle_proyecto",
        id=proyecto_id
    )


@login_required
def exportar_materiales_proyecto_excel(request, proyecto_id):
    """
    Genera y descarga un archivo Excel (.xlsx) con el consolidado
    exclusivo de los materiales requeridos y sus cantidades para el proyecto.
    """
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    # Consultar materiales requeridos e instalados en los apoyos de este proyecto
    req_qs = (
        ApoyoMaterial.objects.filter(apoyo__proyecto=proyecto)
        .values("material__item", "material__descripcion", "material__unidad")
        .annotate(total_requerido=Sum("cantidad_requerida"))
        .order_by("material__descripcion")
    )

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Materiales Requeridos"

    # Estilos
    font_titulo = Font(name="Calibri", size=14, bold=True, color="1E3A8A")
    font_subtitulo = Font(name="Calibri", size=10, bold=True, color="4B5563")
    font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    font_data = Font(name="Calibri", size=11, color="111827")
    font_total = Font(name="Calibri", size=11, bold=True, color="1E3A8A")

    fill_header = PatternFill(start_color="1E40AF", end_color="1E40AF", fill_type="solid")
    fill_total = PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid")
    fill_zebra = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

    thin_border_side = Side(border_style="thin", color="CBD5E1")
    border_cell = Border(
        left=thin_border_side,
        right=thin_border_side,
        top=thin_border_side,
        bottom=thin_border_side
    )
    border_total = Border(
        top=Side(border_style="medium", color="1E40AF"),
        bottom=Side(border_style="double", color="1E40AF"),
        left=thin_border_side,
        right=thin_border_side
    )

    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")

    # Encabezado del documento
    ws.merge_cells("A1:D1")
    ws["A1"] = "COINTECA S.A.S. — MATERIALES REQUERIDOS"
    ws["A1"].font = font_titulo
    ws["A1"].alignment = align_left

    ws.merge_cells("A2:D2")
    ws["A2"] = f"PROYECTO: {proyecto.numero_emcali}  |  TIPO: {proyecto.tipo}  |  ESTADO: {proyecto.estado}  |  FECHA: {timezone.now().strftime('%d/%m/%Y')}"
    ws["A2"].font = font_subtitulo
    ws["A2"].alignment = align_left

    # Fila vacía
    ws.append([])

    # Encabezados de tabla
    headers = ["ÍTEM", "DESCRIPCIÓN DEL MATERIAL", "UNIDAD", "CANTIDAD REQUERIDA"]
    ws.append(headers)
    header_row = 4

    for col_idx in range(1, 5):
        cell = ws.cell(row=header_row, column=col_idx)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = align_center if col_idx != 2 else align_left
        cell.border = border_cell

    # Filas de datos
    current_row = header_row + 1
    total_general = Decimal("0")

    for idx, item in enumerate(req_qs, start=1):
        cant = item["total_requerido"] or Decimal("0")
        total_general += cant
        unidad = item["material__unidad"] or "U"

        ws.append([
            item["material__item"],
            item["material__descripcion"],
            unidad,
            float(cant)
        ])

        for col_idx in range(1, 5):
            c = ws.cell(row=current_row, column=col_idx)
            c.font = font_data
            c.border = border_cell
            if idx % 2 == 0:
                c.fill = fill_zebra

            if col_idx == 1:
                c.alignment = align_center
            elif col_idx == 2:
                c.alignment = align_left
            elif col_idx == 3:
                c.alignment = align_center
            elif col_idx == 4:
                c.alignment = align_right
                c.number_format = "#,##0.00"

        current_row += 1

    # Fila de totales
    ws.append(["", "TOTAL GENERAL REQUERIDO", f"{len(req_qs)} ÍTEMS", float(total_general)])
    for col_idx in range(1, 5):
        c = ws.cell(row=current_row, column=col_idx)
        c.font = font_total
        c.fill = fill_total
        c.border = border_total
        if col_idx in [1, 3]:
            c.alignment = align_center
        elif col_idx == 2:
            c.alignment = align_left
        elif col_idx == 4:
            c.alignment = align_right
            c.number_format = "#,##0.00"

    # Ajuste de anchos de columna
    ws.column_dimensions["A"].width = 12
    ws.column_dimensions["B"].width = 50
    ws.column_dimensions["C"].width = 15
    ws.column_dimensions["D"].width = 24

    # Generar respuesta HTTP con el archivo binario Excel
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    filename = f"Materiales_Requeridos_Proyecto_{proyecto.numero_emcali}.xlsx"
    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
