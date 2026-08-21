from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from decimal import Decimal
from core.models import (
    Proyecto,
    Material,
    Apoyo,
    ApoyoMaterial,
    EntradaMaterialProyecto,
    DetalleEntradaMaterial,
    ConsumoMaterialProyecto,
    DetalleConsumoMaterial,
)
from django.db import transaction
from django.contrib.auth.decorators import login_required

@login_required
def proyectos_logistica(request):
    """
    Vista principal de Proyectos y Control de Materiales en Logística.
    Muestra el listado de proyectos con indicadores de entradas y consumo en obra.
    """
    proyectos = Proyecto.objects.all().order_by("-id")

    resumen_proyectos = []
    for p in proyectos:
        num_entradas = p.entradas_material.count()
        num_consumos = p.consumos_material.count()
        resumen_proyectos.append({
            "proyecto": p,
            "num_entradas": num_entradas,
            "num_consumos": num_consumos,
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
    Calcula la matriz comparativa:
    [ Requerido (Ingeniería) | Entrado (Logística) | Consumido (Supervisor) | Saldo Terreno | Alerta ]
    """
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    # 1. Agregaciones grupales en 3 consultas eficientes
    req_qs = (
        ApoyoMaterial.objects.filter(apoyo__proyecto=proyecto)
        .values("material_id")
        .annotate(total=Sum("cantidad_requerida"))
    )
    req_map = {item["material_id"]: item["total"] for item in req_qs}

    ent_qs = (
        DetalleEntradaMaterial.objects.filter(entrada__proyecto=proyecto)
        .values("material_id")
        .annotate(total=Sum("cantidad"))
    )
    ent_map = {item["material_id"]: item["total"] for item in ent_qs}

    con_qs = (
        DetalleConsumoMaterial.objects.filter(consumo__proyecto=proyecto)
        .values("material_id")
        .annotate(total=Sum("cantidad"))
    )
    con_map = {item["material_id"]: item["total"] for item in con_qs}

    # 2. Obtener todos los materiales involucrados en el proyecto
    all_material_ids = set(req_map.keys()) | set(ent_map.keys()) | set(con_map.keys())
    materiales_db = Material.objects.filter(id__in=all_material_ids).order_by("descripcion")

    balance_materiales = []
    total_items_requeridos = Decimal("0")
    total_items_entrados = Decimal("0")
    total_items_consumidos = Decimal("0")

    # 3. Construcción del balance para la plantilla
    for mat in materiales_db:
        sum_req = req_map.get(mat.id, Decimal("0"))
        sum_ent = ent_map.get(mat.id, Decimal("0"))
        sum_con = con_map.get(mat.id, Decimal("0"))

        saldo = sum_ent - sum_con
        diferencia_req = sum_con - sum_req if sum_req > 0 else Decimal("0")

        pct_consumo = (
            round((sum_con / sum_ent * Decimal("100")), 1) 
            if sum_ent > 0 
            else (Decimal("100.0") if sum_con > 0 else Decimal("0.0"))
        )

        if sum_con > sum_ent:
            estado_alerta = "excedido"
            badge_texto = "Consumo > Entrada"
            badge_color = "bg-red-100 text-red-800 border-red-300"
        elif sum_req > 0 and sum_con > sum_req:
            estado_alerta = "excede_ingenieria"
            badge_texto = "Excede Ingeniería"
            badge_color = "bg-yellow-100 text-yellow-800 border-yellow-300"
        elif sum_ent > 0 and saldo == 0:
            estado_alerta = "cerrado"
            badge_texto = "Todo Utilizado"
            badge_color = "bg-blue-100 text-blue-800 border-blue-300"
        elif saldo > 0:
            estado_alerta = "disponible"
            badge_texto = f"Saldo: {saldo}"
            badge_color = "bg-green-100 text-green-800 border-green-300"
        else:
            estado_alerta = "pendiente"
            badge_texto = "Sin Entradas"
            badge_color = "bg-gray-100 text-gray-700 border-gray-300"

        balance_materiales.append({
            "material": mat,
            "requerido": sum_req,
            "entrada": sum_ent,
            "consumo": sum_con,
            "saldo": saldo,
            "diferencia_req": diferencia_req,
            "pct_consumo": pct_consumo,
            "estado_alerta": estado_alerta,
            "badge_texto": badge_texto,
            "badge_color": badge_color,
        })

        total_items_requeridos += sum_req
        total_items_entrados += sum_ent
        total_items_consumidos += sum_con

    entradas = (
        EntradaMaterialProyecto.objects.filter(proyecto=proyecto)
        .prefetch_related("detalles__material")
        .order_by("-fecha", "-id")
    )
    consumos = (
        ConsumoMaterialProyecto.objects.filter(proyecto=proyecto)
        .prefetch_related("detalles__material")
        .order_by("-fecha_reporte", "-id")
    )

    return render(
        request,
        "logistica/proyectos/detalle_proyecto.html",
        {
            "proyecto": proyecto,
            "balance_materiales": balance_materiales,
            "entradas": entradas,
            "consumos": consumos,
            "total_items_requeridos": total_items_requeridos,
            "total_items_entrados": total_items_entrados,
            "total_items_consumidos": total_items_consumidos,
            "saldo_total_items": total_items_entrados - total_items_consumidos,
        },
    )

@login_required
@transaction.atomic
def registrar_entrada_material(request, proyecto_id):
    """
    Registra una remisión/factura de entrada de materiales directamente para el proyecto.
    """
    
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    materiales = Material.objects.all().order_by("descripcion")

    if request.method == "POST":
        fecha = request.POST.get("fecha")
        if fecha:
            entrada = EntradaMaterialProyecto.objects.create(
                proyecto=proyecto,
                fecha=fecha,
                proveedor=request.POST.get("proveedor", "").strip(),
                numero_remision=request.POST.get("numero_remision", "").strip(),
                recibido_por=request.POST.get("recibido_por", "").strip(),
                observaciones=request.POST.get("observaciones", "").strip(),
            )

            material_ids = request.POST.getlist("material_id[]")
            cantidades = request.POST.getlist("cantidad[]")

            detalles = []
            for mat_id, cant_str in zip(material_ids, cantidades):
                try:
                    cant = Decimal(cant_str.strip())
                    if cant > 0 and mat_id:
                        detalles.append(
                            DetalleEntradaMaterial(
                                entrada=entrada,
                                material_id=mat_id,
                                cantidad=cant
                            )
                        )
                except (ValueError, TypeError):
                    continue

            if detalles:
                DetalleEntradaMaterial.objects.bulk_create(detalles)

            return redirect("detalle_proyecto_logistica", proyecto_id=proyecto.id)

    return render(
        request,
        "logistica/proyectos/crear_entrada.html",
        {"proyecto": proyecto, "materiales": materiales},
    )

@login_required
def eliminar_entrada_material(request, entrada_id):
    """
    Elimina una entrada de material y sus detalles.
    """
    entrada = get_object_or_404(EntradaMaterialProyecto, id=entrada_id)
    proyecto_id = entrada.proyecto.id

    if request.method == "POST":
        entrada.delete()

    return redirect("detalle_proyecto_logistica", proyecto_id=proyecto_id)

@login_required
@transaction.atomic
def registrar_consumo_material(request, proyecto_id):
    """
    Digitaliza el reporte/planilla física del supervisor con los materiales consumidos en obra.
    """
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    materiales = Material.objects.all().order_by("descripcion")

    if request.method == "POST":
        fecha_reporte = request.POST.get("fecha_reporte")
        if fecha_reporte:
            consumo = ConsumoMaterialProyecto.objects.create(
                proyecto=proyecto,
                fecha_reporte=fecha_reporte,
                reportado_por=request.POST.get("reportado_por", "").strip(),
                frente_trabajo=request.POST.get("frente_trabajo", "").strip(),
                observaciones=request.POST.get("observaciones", "").strip(),
            )

            material_ids = request.POST.getlist("material_id[]")
            cantidades = request.POST.getlist("cantidad[]")

            detalles = []
            for mat_id, cant_str in zip(material_ids, cantidades):
                try:
                    cant = Decimal(cant_str.strip())
                    if cant > 0 and mat_id:
                        detalles.append(
                            DetalleConsumoMaterial(
                                consumo=consumo,
                                material_id=mat_id,
                                cantidad=cant
                            )
                        )
                except (ValueError, TypeError):
                    continue

            if detalles:
                DetalleConsumoMaterial.objects.bulk_create(detalles)

            return redirect("detalle_proyecto_logistica", proyecto_id=proyecto.id)

    return render(
        request,
        "logistica/proyectos/crear_consumo.html",
        {"proyecto": proyecto, "materiales": materiales},
    )

@login_required
def eliminar_consumo_material(request, consumo_id):
    """
    Elimina un reporte de consumo y sus detalles.
    """
    consumo = get_object_or_404(ConsumoMaterialProyecto, id=consumo_id)
    proyecto_id = consumo.proyecto.id

    if request.method == "POST":
        consumo.delete()

    return redirect("detalle_proyecto_logistica", proyecto_id=proyecto_id)
