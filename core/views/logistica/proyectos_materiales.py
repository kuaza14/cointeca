import io
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal
from core.models import (
    Proyecto,
    Material,
    Apoyo,
    ApoyoMaterial,
    EntradaMaterialProyecto,
    DetalleEntradaMaterial,
    MaterialRequeridoProyecto,
    Inventario,
)
from django.db import transaction
from django.contrib.auth.decorators import login_required



@login_required
def proyectos_logistica(request):
    """
    Vista principal de Proyectos y Control de Materiales en Logística.
    Muestra el listado de proyectos con indicadores de entradas y materiales en obra.
    """
    proyectos = Proyecto.objects.all().order_by("-id")

    resumen_proyectos = []
    for p in proyectos:
        num_entradas = p.entradas_material.count()
        num_apoyos = p.apoyos.count()
        total_items_instalados = ApoyoMaterial.objects.filter(apoyo__proyecto=p).count()
        resumen_proyectos.append({
            "proyecto": p,
            "num_entradas": num_entradas,
            "num_apoyos": num_apoyos,
            "total_items_instalados": total_items_instalados,
        })

    return render(
        request,
        "logistica/proyectos/lista_proyectos.html",
        {
            "resumen_proyectos": resumen_proyectos,
            "total_proyectos": proyectos.count(),
        }
    )


@login_required
def detalle_proyecto_logistica(request, proyecto_id):
    """
    Tablero de control de materiales para un proyecto específico.
    Calcula la matriz comparativa en tiempo real:
    [ Requerido/Instalado en Apoyos | Stock Bodega | Entrado/Despachado | Saldo en Terreno | % Abastecido ]
    """
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    # 1. Requerido / Consumo en Obra (viene directamente de los Apoyos de Ingeniería)
    req_qs = (
        MaterialRequeridoProyecto.objects
        .filter(proyecto=proyecto)
        .values("material_id")
        .annotate(total=Sum("cantidad_requerida"))
    )

    req_map = {
        item["material_id"]: item["total"]
        for item in req_qs
    }

    # 2. Entradas Suministradas (compras de proveedor o despachos de bodega)
    ent_qs = (
        DetalleEntradaMaterial.objects.filter(entrada__proyecto=proyecto)
        .values("material_id")
        .annotate(total=Sum("cantidad"))
    )
    ent_map = {item["material_id"]: item["total"] for item in ent_qs}

    # 3. Obtener todos los materiales involucrados en el proyecto
    all_material_ids = set(req_map.keys()) | set(ent_map.keys())
    materiales_db = Material.objects.filter(id__in=all_material_ids).select_related("inventario").order_by("descripcion")

    balance_materiales = []
    total_items_requeridos = Decimal("0")
    total_items_entrados = Decimal("0")

    for mat in materiales_db:
        sum_req = req_map.get(mat.id, Decimal("0"))
        sum_ent = ent_map.get(mat.id, Decimal("0"))
        stock_bodega = getattr(mat, "inventario", None)
        stock_disponible = stock_bodega.cantidad if stock_bodega else Decimal("0")
        saldo_terreno = sum_ent - sum_req

        balance_materiales.append({
            "material": mat,
            "requerido": sum_req,
            "stock_bodega": stock_disponible,
            "entrada": sum_ent,
            "saldo_terreno": saldo_terreno,
        })

        total_items_requeridos += sum_req
        total_items_entrados += sum_ent

    entradas = (
        EntradaMaterialProyecto.objects.filter(proyecto=proyecto)
        .prefetch_related("detalles__material")
        .order_by("-fecha", "-id")
    )

    return render(
        request,
        "logistica/proyectos/detalle_proyecto.html",
        {
            "proyecto": proyecto,
            "balance_materiales": balance_materiales,
            "entradas": entradas,
            "total_items_requeridos": total_items_requeridos,
            "total_items_entrados": total_items_entrados,
            "saldo_total_items": total_items_entrados - total_items_requeridos,
        }
    )

@login_required
@transaction.atomic
def registrar_entrada_material(request, proyecto_id):
    proyecto = get_object_or_404(
        Proyecto,
        id=proyecto_id
    )
    materiales = Material.objects.all().order_by("descripcion")

    entradas = (
        EntradaMaterialProyecto.objects
        .filter(proyecto=proyecto)
        .prefetch_related("detalles__material")
    )

    req_qs = (
        MaterialRequeridoProyecto.objects
        .filter(proyecto=proyecto)
        .select_related("material")
        .order_by("material__descripcion")
    )

    ent_qs = (
        DetalleEntradaMaterial.objects
        .filter(entrada__proyecto=proyecto)
        .values("material_id")
        .annotate(total_entrado=Sum("cantidad"))
    )

    ent_map = {
        item["material_id"]: item["total_entrado"]
        for item in ent_qs
    }

    materiales_requeridos = []
    for req in req_qs:
        m_id = req.material_id
        req_val = req.cantidad_requerida
        ent_val = ent_map.get(
            m_id,
            Decimal("0")
        )

        pendiente = max(
            Decimal("0"),
            req_val - ent_val
        )

        materiales_requeridos.append({
            "material_id": m_id,
            "item": req.material.item,
            "descripcion": req.material.descripcion,
            "unidad": req.material.unidad or "UN",
            "requerido": req_val,
            "entrado": ent_val,
            "pendiente": pendiente,
        })


    if request.method == "POST":
        fecha = request.POST.get("fecha")
        if fecha:
            entrada = EntradaMaterialProyecto.objects.create(
                proyecto=proyecto,
                fecha=fecha,
                proveedor=request.POST.get(
                    "proveedor",
                    ""
                ).strip(),
                numero_remision=request.POST.get(
                    "numero_remision",
                    ""
                ).strip(),
                recibido_por=request.POST.get(
                    "recibido_por",
                    ""
                ).strip(),
                observaciones=request.POST.get(
                    "observaciones",
                    ""
                ).strip(),
            )

            material_ids = request.POST.getlist(
                "material_id[]"
            )

            cantidades = request.POST.getlist(
                "cantidad[]"
            )
            detalles = []

            for mat_id, cant_str in zip(
                material_ids,
                cantidades
            ):

                try:

                    cant = Decimal(
                        cant_str.strip()
                    )
                    if cant > 0 and mat_id:
                        detalles.append(
                            DetalleEntradaMaterial(
                                entrada=entrada,
                                material_id=mat_id,
                                cantidad=cant
                            )
                        )

                except (
                    ValueError,
                    TypeError,
                    Decimal.InvalidOperation
                ):
                    continue

            if detalles:
                DetalleEntradaMaterial.objects.bulk_create(
                    detalles
                )

                for mat_id, cant_str in zip(
                    material_ids,
                    cantidades
                ):
                    try:
                        cant = Decimal(
                            cant_str.strip()
                        )
                        if cant > 0 and mat_id:
                            inventario, creado = (
                                Inventario.objects.get_or_create(
                                    material_id=mat_id,
                                    defaults={
                                        "cantidad": Decimal("0")
                                    }
                                )
                            )
                            inventario.cantidad += cant
                            inventario.save(
                                update_fields=["cantidad"]
                            )

                    except (
                        ValueError,
                        TypeError,
                        Decimal.InvalidOperation
                    ):
                        continue
            return redirect(
                "registrar_entrada_material",
                proyecto_id=proyecto.id
            )
    entradas = (
        EntradaMaterialProyecto.objects
        .filter(proyecto=proyecto)
        .prefetch_related("detalles__material")
        .order_by("-fecha", "-id")
    )

    return render(
        request,
        "logistica/proyectos/crear_entrada.html",
        {
            "proyecto": proyecto,
            "materiales": materiales,
            "materiales_requeridos": materiales_requeridos,
            "entradas": entradas,
        }
    )

@login_required
def materiales_requeridos_proyecto(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    materiales_requeridos = (
        MaterialRequeridoProyecto.objects
        .filter(proyecto=proyecto)
        .select_related("material")
        .order_by("material__item")
    )

    materiales = Material.objects.all().order_by("item")

    if request.method == "POST":
        accion = request.POST.get("accion")

        # ==========================
        # AGREGAR MATERIAL
        # ==========================
        if accion == "agregar":
            material_id = request.POST.get("material_id")
            cantidad_str = request.POST.get("cantidad")

            try:
                cantidad = Decimal(cantidad_str)

                if material_id and cantidad > 0:
                    material = get_object_or_404(
                        Material,
                        id=material_id
                    )

                    # Evitar duplicados
                    requerido, creado = (
                        MaterialRequeridoProyecto.objects.get_or_create(
                            proyecto=proyecto,
                            material=material,
                            defaults={
                                "cantidad_requerida": cantidad
                            }
                        )
                    )

                    # Si ya existía, no lo duplicamos.
                    # Más adelante podemos decidir si mostramos
                    # un mensaje de "ya existe".
                    if not creado:
                        requerido.cantidad_requerida = cantidad
                        requerido.save()

            except (ValueError, TypeError, Decimal.InvalidOperation):
                pass

            return redirect(
                "materiales_requeridos_proyecto",
                proyecto_id=proyecto.id
            )

        # ==========================
        # EDITAR CANTIDAD
        # ==========================
        elif accion == "editar":
            requerido_id = request.POST.get("requerido_id")
            cantidad_str = request.POST.get("cantidad")

            requerido = get_object_or_404(
                MaterialRequeridoProyecto,
                id=requerido_id,
                proyecto=proyecto
            )

            try:
                cantidad = Decimal(cantidad_str)

                if cantidad > 0:
                    requerido.cantidad_requerida = cantidad
                    requerido.save()

            except (ValueError, TypeError, Decimal.InvalidOperation):
                pass

            return redirect(
                "materiales_requeridos_proyecto",
                proyecto_id=proyecto.id
            )

        elif accion == "eliminar":
            requerido_id = request.POST.get("requerido_id")

            requerido = get_object_or_404(
                MaterialRequeridoProyecto,
                id=requerido_id,
                proyecto=proyecto
            )

            requerido.delete()

            return redirect(
                "materiales_requeridos_proyecto",
                proyecto_id=proyecto.id
            )

    total_requerido = (
        materiales_requeridos.aggregate(
            total=Sum("cantidad_requerida")
        )["total"]
        or Decimal("0")
    )

    return render(
        request,
        "logistica/proyectos/materiales_requeridos.html",
        {
            "proyecto": proyecto,
            "materiales_catalogo": materiales,
            "lista_requeridos": materiales_requeridos,
            "total_items": materiales_requeridos.count(),
            "total_cantidad": total_requerido,
        }
    )

@login_required
@transaction.atomic
def eliminar_entrada_material(request, entrada_id):
    entrada = get_object_or_404(
        EntradaMaterialProyecto,
        id=entrada_id
    )

    proyecto_id = entrada.proyecto.id
    if request.method == "POST":
        detalles = entrada.detalles.select_related(
            "material"
        )

        for detalle in detalles:

            inventario = Inventario.objects.filter(
                material=detalle.material
            ).first()

            if inventario:
                inventario.cantidad -= detalle.cantidad

                if inventario.cantidad < 0:
                    inventario.cantidad = Decimal("0")

                inventario.save(
                    update_fields=["cantidad"]
                )

        entrada.delete()

    return redirect(
        "registrar_entrada_material",
        proyecto_id=proyecto_id
    )

@login_required
@transaction.atomic
def editar_entrada_material(request, entrada_id):

    entrada = get_object_or_404(
        EntradaMaterialProyecto,
        id=entrada_id
    )

    proyecto = entrada.proyecto

    if request.method == "POST":

        # ==========================================
        # DATOS DE LA ENTRADA
        # ==========================================

        entrada.fecha = request.POST.get("fecha")

        entrada.numero_remision = request.POST.get(
            "numero_remision",
            ""
        ).strip()

        entrada.proveedor = request.POST.get(
            "proveedor",
            ""
        ).strip()

        entrada.recibido_por = request.POST.get(
            "recibido_por",
            ""
        ).strip()

        entrada.observaciones = request.POST.get(
            "observaciones",
            ""
        ).strip()

        entrada.save()

        # ==========================================
        # MATERIALES
        # ==========================================

        material_ids = request.POST.getlist(
            "material_id[]"
        )

        cantidades = request.POST.getlist(
            "cantidad[]"
        )

        # Materiales que quedan después de editar
        nuevos_materiales = {}

        for mat_id, cantidad_str in zip(
            material_ids,
            cantidades
        ):

            if not mat_id:
                continue

            try:
                cantidad = Decimal(
                    cantidad_str.strip()
                )
            except (
                ValueError,
                TypeError,
                Decimal.InvalidOperation
            ):
                continue

            if cantidad <= 0:
                continue

            # Si el mismo material aparece dos veces,
            # sumamos las cantidades.
            nuevos_materiales[mat_id] = (
                nuevos_materiales.get(
                    mat_id,
                    Decimal("0")
                )
                + cantidad
            )

        # ==========================================
        # CANTIDADES ANTERIORES
        # ==========================================

        materiales_anterior = {}

        detalles_actuales = entrada.detalles.all()

        for detalle in detalles_actuales:

            mat_id = str(
                detalle.material_id
            )

            materiales_anterior[mat_id] = (
                materiales_anterior.get(
                    mat_id,
                    Decimal("0")
                )
                + detalle.cantidad
            )

        # ==========================================
        # ACTUALIZAR INVENTARIO
        # ==========================================

        todos_los_materiales = set(
            materiales_anterior.keys()
        ) | set(
            nuevos_materiales.keys()
        )

        for mat_id in todos_los_materiales:

            cantidad_anterior = materiales_anterior.get(
                str(mat_id),
                Decimal("0")
            )

            cantidad_nueva = nuevos_materiales.get(
                str(mat_id),
                Decimal("0")
            )

            diferencia = (
                cantidad_nueva
                - cantidad_anterior
            )

            if diferencia == 0:
                continue

            inventario, creado = (
                Inventario.objects.get_or_create(
                    material_id=mat_id,
                    defaults={
                        "cantidad": Decimal("0")
                    }
                )
            )

            inventario.cantidad += diferencia

            if inventario.cantidad < 0:
                inventario.cantidad = Decimal("0")

            inventario.save(
                update_fields=["cantidad"]
            )

        # ==========================================
        # REEMPLAZAR DETALLES
        # ==========================================

        entrada.detalles.all().delete()

        nuevos_detalles = []

        for mat_id, cantidad in nuevos_materiales.items():

            nuevos_detalles.append(
                DetalleEntradaMaterial(
                    entrada=entrada,
                    material_id=mat_id,
                    cantidad=cantidad
                )
            )

        if nuevos_detalles:

            DetalleEntradaMaterial.objects.bulk_create(
                nuevos_detalles
            )

        return redirect(
            "registrar_entrada_material",
            proyecto_id=proyecto.id
        )

    # ==========================================
    # MOSTRAR FORMULARIO DE EDICIÓN
    # ==========================================

    detalles = entrada.detalles.select_related(
        "material"
    ).all()

    materiales = Material.objects.all().order_by(
        "descripcion"
    )

    return render(
        request,
        "logistica/proyectos/editar_entrada.html",
        {
            "entrada": entrada,
            "proyecto": proyecto,
            "detalles": detalles,
            "materiales": materiales,
        }
    )


@login_required
def materiales_requeridos_proyecto(request, proyecto_id):
    """
    Vista de Materiales Requeridos para un proyecto en Logística.
    Permite consultar, agregar requerimientos y descargar/imprimir el Excel.
    """
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    materiales_catalogo = Material.objects.all().order_by("descripcion")

    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion in ["agregar_requerido", "agregar"]:
            material_ids = request.POST.getlist("material_id[]")
            cantidades = request.POST.getlist("cantidad[]")

            # Soporte por si se envía un único campo
            if not material_ids:
                single_mat = request.POST.get("material_id")
                single_cant = request.POST.get("cantidad")
                if single_mat:
                    material_ids = [single_mat]
                    cantidades = [single_cant]

            for m_id, c_str in zip(material_ids, cantidades):
                if not m_id or not c_str:
                    continue
                try:
                    cant = Decimal(str(c_str).strip())
                    if cant > 0:
                        req, created = MaterialRequeridoProyecto.objects.get_or_create(
                            proyecto=proyecto,
                            material_id=m_id,
                            defaults={"cantidad_requerida": cant}
                        )
                        if not created:
                            req.cantidad_requerida += cant
                            req.save()
                except (ValueError, TypeError, Decimal.InvalidOperation):
                    continue

            return redirect("materiales_requeridos_proyecto", proyecto_id=proyecto.id)

        elif accion in ["eliminar_requerido", "eliminar"]:
            req_id = request.POST.get("req_id") or request.POST.get("requerido_id")
            if req_id:
                MaterialRequeridoProyecto.objects.filter(id=req_id, proyecto=proyecto).delete()

            return redirect("materiales_requeridos_proyecto", proyecto_id=proyecto.id)


    # Consolidar requerimientos (de MaterialRequeridoProyecto y de ApoyoMaterial)
    req_directos = MaterialRequeridoProyecto.objects.filter(proyecto=proyecto).select_related("material")
    
    req_apoyos = (
        ApoyoMaterial.objects.filter(apoyo__proyecto=proyecto)
        .values("material_id", "material__item", "material__descripcion", "material__unidad")
        .annotate(total_apoyo=Sum("cantidad_requerida"))
    )

    mapa_requeridos = {}
    for r in req_directos:
        mapa_requeridos[r.material.id] = {
            "id": r.id,
            "material": r.material,
            "cantidad": r.cantidad_requerida,
            "origen": "Requerido General",
        }

    for a in req_apoyos:
        m_id = a["material_id"]
        if m_id in mapa_requeridos:
            mapa_requeridos[m_id]["cantidad"] += a["total_apoyo"]
        else:
            mat = Material.objects.get(id=m_id)
            mapa_requeridos[m_id] = {
                "id": None,
                "material": mat,
                "cantidad": a["total_apoyo"],
                "origen": "Apoyos Ingeniería",
            }

    lista_requeridos = sorted(mapa_requeridos.values(), key=lambda x: x["material"].descripcion)
    total_cantidad = sum(x["cantidad"] for x in lista_requeridos)

    return render(
        request,
        "logistica/proyectos/materiales_requeridos.html",
        {
            "proyecto": proyecto,
            "materiales_catalogo": materiales_catalogo,
            "lista_requeridos": lista_requeridos,
            "total_cantidad": total_cantidad,
            "total_items": len(lista_requeridos),
        }
    )


@login_required
def exportar_materiales_proyecto_excel(request, proyecto_id):
    """
    Genera y descarga un archivo Excel (.xlsx) con los materiales requeridos
    y sus cantidades exactas (sin ceros ni decimales sobrantes).
    """
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    # Consolidar requerimientos
    req_directos = MaterialRequeridoProyecto.objects.filter(proyecto=proyecto).select_related("material")
    req_apoyos = (
        ApoyoMaterial.objects.filter(apoyo__proyecto=proyecto)
        .values("material_id", "material__item", "material__descripcion", "material__unidad")
        .annotate(total_apoyo=Sum("cantidad_requerida"))
    )

    mapa_requeridos = {}
    for r in req_directos:
        mapa_requeridos[r.material.id] = {
            "item": r.material.item,
            "descripcion": r.material.descripcion,
            "unidad": r.material.unidad or "U",
            "cantidad": r.cantidad_requerida,
        }

    for a in req_apoyos:
        m_id = a["material_id"]
        if m_id in mapa_requeridos:
            mapa_requeridos[m_id]["cantidad"] += a["total_apoyo"]
        else:
            mapa_requeridos[m_id] = {
                "item": a["material__item"],
                "descripcion": a["material__descripcion"],
                "unidad": a["material__unidad"] or "U",
                "cantidad": a["total_apoyo"],
            }

    lista_items = sorted(mapa_requeridos.values(), key=lambda x: x["descripcion"])

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Materiales Requeridos"

    font_titulo = Font(name="Calibri", size=14, bold=True, color="1E3A8A")
    font_subtitulo = Font(name="Calibri", size=10, bold=True, color="4B5563")
    font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    font_data = Font(name="Calibri", size=11, color="111827")
    font_total = Font(name="Calibri", size=11, bold=True, color="1E3A8A")

    fill_header = PatternFill(start_color="1E40AF", end_color="1E40AF", fill_type="solid")
    fill_total = PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid")
    fill_zebra = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

    thin_border_side = Side(border_style="thin", color="CBD5E1")
    border_cell = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
    border_total = Border(
        top=Side(border_style="medium", color="1E40AF"),
        bottom=Side(border_style="double", color="1E40AF"),
        left=thin_border_side,
        right=thin_border_side
    )

    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")

    # Encabezado
    ws.merge_cells("A1:D1")
    ws["A1"] = "COINTECA S.A.S. — MATERIALES REQUERIDOS"
    ws["A1"].font = font_titulo
    ws["A1"].alignment = align_left

    ws.merge_cells("A2:D2")
    ws["A2"] = f"PROYECTO: {proyecto.numero_emcali}  |  TIPO: {proyecto.tipo}  |  ESTADO: {proyecto.estado}  |  FECHA: {timezone.now().strftime('%d/%m/%Y')}"
    ws["A2"].font = font_subtitulo
    ws["A2"].alignment = align_left

    ws.append([])

    headers = ["ÍTEM", "DESCRIPCIÓN DEL MATERIAL", "UNIDAD", "CANTIDAD REQUERIDA"]
    ws.append(headers)
    header_row = 4

    for col_idx in range(1, 5):
        cell = ws.cell(row=header_row, column=col_idx)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = align_center if col_idx != 2 else align_left
        cell.border = border_cell

    current_row = header_row + 1
    total_general = Decimal("0")

    for idx, item in enumerate(lista_items, start=1):
        cant = item["cantidad"] or Decimal("0")
        total_general += cant

        # Si es un número entero exacto (ej: 10.0), mostrarlo como entero (10)
        # Si tiene decimales (ej: 2.5), mostrar exactamente 2.5
        if cant % 1 == 0:
            cant_formateada = int(cant)
            formato_num = "#,##0"
        else:
            cant_formateada = float(cant)
            formato_num = "0.##"

        ws.append([
            item["item"],
            item["descripcion"],
            item["unidad"],
            cant_formateada
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
                c.number_format = formato_num

        current_row += 1

    # Fila total general
    if total_general % 1 == 0:
        total_formateado = int(total_general)
        formato_total = "#,##0"
    else:
        total_formateado = float(total_general)
        formato_total = "0.##"

    ws.append(["", "TOTAL GENERAL REQUERIDO", f"{len(lista_items)} ÍTEMS", total_formateado])
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
            c.number_format = formato_total

    ws.column_dimensions["A"].width = 12
    ws.column_dimensions["B"].width = 50
    ws.column_dimensions["C"].width = 15
    ws.column_dimensions["D"].width = 24

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