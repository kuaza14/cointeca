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
        sum_req = req_map.get(mat.id, Decimal("0"))      # Lo que se necesita / usa en los apoyos
        sum_ent = ent_map.get(mat.id, Decimal("0"))      # Lo que ha entrado/despachado a la obra
        stock_bodega = getattr(mat, "inventario", None)
        stock_disponible = stock_bodega.cantidad if stock_bodega else Decimal("0")

        saldo_terreno = sum_ent - sum_req                # Saldo en obra (Entrado - Requerido/Instalado)

        # % Abastecido respecto a lo requerido
        if sum_req > 0:
            pct_abastecido = round((sum_ent / sum_req * Decimal("100")), 1)
        else:
            pct_abastecido = Decimal("100.0") if sum_ent > 0 else Decimal("0.0")

        # Alerta visual
        if sum_ent < sum_req:
            estado_alerta = "falta_material"
            badge_texto = f"Faltan {sum_req - sum_ent}"
            badge_color = "bg-amber-100 text-amber-800 border-amber-300"
        elif sum_ent > sum_req:
            estado_alerta = "excedido"
            badge_texto = f"Sobrante: +{sum_ent - sum_req}"
            badge_color = "bg-blue-100 text-blue-800 border-blue-300"
        elif sum_ent > 0 and sum_ent == sum_req:
            estado_alerta = "completo"
            badge_texto = "100% Abastecido"
            badge_color = "bg-green-100 text-green-800 border-green-300"
        else:
            estado_alerta = "sin_entradas"
            badge_texto = "Sin Entradas"
            badge_color = "bg-red-100 text-red-700 border-red-300"

        balance_materiales.append({
            "material": mat,
            "requerido": sum_req,
            "stock_bodega": stock_disponible,
            "entrada": sum_ent,
            "saldo_terreno": saldo_terreno,
            "pct_abastecido": pct_abastecido,
            "estado_alerta": estado_alerta,
            "badge_texto": badge_texto,
            "badge_color": badge_color,
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
            "materiales": materiales,
            "materiales_requeridos": materiales_requeridos,
            "total_requerido": total_requerido,
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