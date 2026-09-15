import io
import json
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Sum, Q
from decimal import Decimal
from django.contrib import messages
from core.models import (
    Macroproyecto,
    Proyecto,
    Material,
    Apoyo,
    ApoyoMaterial,
    EntradaMaterialProyecto,
    DetalleEntradaMaterial,
    RetiroMaterialProyecto,
    DetalleRetiroMaterial,
    MaterialRequeridoProyecto,
    Inventario,
)
from django.db import transaction
from django.contrib.auth.decorators import login_required

@login_required
def macroproyectos_logistica(request):
    """
    Vista principal de Macroproyectos en Logística.
    Agrupa los proyectos por Macroproyecto con métricas consolidadas.
    """
    query = request.GET.get("q", "").strip()
    macroproyectos = Macroproyecto.objects.all().prefetch_related("proyectos")

    if query:
        macroproyectos = macroproyectos.filter(
            Q(nombre__icontains=query) |
            Q(numero_maniobra_emcali__icontains=query) |
            Q(numero_maniobra_cointeca__icontains=query) |
            Q(descripcion__icontains=query) |
            Q(estado__icontains=query)
        )

    resumen_macros = []
    for macro in macroproyectos:
        proyectos_macro = macro.proyectos.all()
        num_proyectos = proyectos_macro.count()
        num_entradas = EntradaMaterialProyecto.objects.filter(proyecto__macroproyecto=macro).count()
        num_apoyos = Apoyo.objects.filter(proyecto__macroproyecto=macro).count()
        num_retiros = ApoyoMaterial.objects.filter(apoyo__proyecto__macroproyecto=macro, cantidad_retirada__gt=0).count()
        
        resumen_macros.append({
            "macro": macro,
            "num_proyectos": num_proyectos,
            "num_entradas": num_entradas,
            "num_apoyos": num_apoyos,
            "num_retiros": num_retiros,
        })

    return render(
        request,
        "logistica/macroproyectos/lista_macroproyectos.html",
        {
            "macroproyectos": resumen_macros,
            "query": query,
            "total_macros": Macroproyecto.objects.count(),
            "total_filtrados": len(resumen_macros),
        }
    )

@login_required
def proyectos_logistica(request, macroproyecto_id=None):
    """
    Listado de proyectos y control de materiales en logística.
    Si se especifica macroproyecto_id, filtra exclusivamente los proyectos de ese macroproyecto.
    """
    macroproyecto = None
    if macroproyecto_id:
        macroproyecto = get_object_or_404(Macroproyecto, id=macroproyecto_id)
        proyectos = Proyecto.objects.filter(macroproyecto=macroproyecto).order_by("-id")
    else:
        macro_param = request.GET.get("macroproyecto_id")
        if macro_param and macro_param.isdigit():
            macroproyecto = Macroproyecto.objects.filter(id=int(macro_param)).first()
            proyectos = Proyecto.objects.filter(macroproyecto=macroproyecto).order_by("-id") if macroproyecto else Proyecto.objects.all().order_by("-id")
        else:
            proyectos = Proyecto.objects.all().order_by("-id")

    query = request.GET.get("q", "").strip()
    if query:
        proyectos = proyectos.filter(
            Q(numero_emcali__icontains=query) |
            Q(tipo__icontains=query) |
            Q(estado__icontains=query)
        )

    resumen_proyectos = []
    for p in proyectos:
        num_entradas = p.entradas_material.count()
        num_retiros = ApoyoMaterial.objects.filter(apoyo__proyecto=p, cantidad_retirada__gt=0).count()
        num_apoyos = p.apoyos.count()
        total_items_instalados = ApoyoMaterial.objects.filter(apoyo__proyecto=p).count()
        resumen_proyectos.append({
            "proyecto": p,
            "num_entradas": num_entradas,
            "num_retiros": num_retiros,
            "num_apoyos": num_apoyos,
            "total_items_instalados": total_items_instalados,
        })

    todos_macroproyectos = Macroproyecto.objects.all().order_by("nombre")

    return render(
        request,
        "logistica/proyectos/lista_proyectos.html",
        {
            "macroproyecto": macroproyecto,
            "resumen_proyectos": resumen_proyectos,
            "total_proyectos": len(resumen_proyectos),
            "query": query,
            "macroproyectos": todos_macroproyectos,
        }
    )


@login_required
def detalle_proyecto_logistica(request, proyecto_id):
    """
    Tablero de control de materiales para un proyecto específico.
    Calcula la matriz comparativa en tiempo real:
    [ Requerido | Instalado en Apoyos | Retirado | Suministrado (Entradas) | Stock Bodega ]
    """
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    if request.method == "POST":
        accion = request.POST.get("accion")
        if accion == "agregar_requerido":
            material_ids = request.POST.getlist("material_id[]")
            cantidades = request.POST.getlist("cantidad[]")
            if not material_ids:
                single_mat = request.POST.get("material_id")
                single_cant = request.POST.get("cantidad")
                if single_mat:
                    material_ids = [single_mat]
                    cantidades = [single_cant]

            agregados = 0
            for m_id, c_str in zip(material_ids, cantidades):
                if not m_id or not c_str:
                    continue
                try:
                    cant_dec = Decimal(str(c_str).strip().replace(',', '.'))
                    if cant_dec > 0:
                        req_obj, created = MaterialRequeridoProyecto.objects.get_or_create(
                            proyecto=proyecto,
                            material_id=int(m_id),
                            defaults={"cantidad_requerida": cant_dec}
                        )
                        if not created:
                            req_obj.cantidad_requerida += cant_dec
                            req_obj.save()
                        agregados += 1
                except Exception:
                    continue

            if agregados > 0:
                messages.success(request, f"Se registraron {agregados} material(es) requerido(s) para este proyecto.")
            return redirect("detalle_proyecto_logistica", proyecto_id=proyecto.id)

        elif accion == "eliminar_requerido":
            req_id = request.POST.get("req_id")
            if req_id:
                MaterialRequeridoProyecto.objects.filter(id=req_id, proyecto=proyecto).delete()
            return redirect("detalle_proyecto_logistica", proyecto_id=proyecto.id)

    # 1. Instalado en Apoyos (Ingeniería)
    apoyo_inst_qs = (
        ApoyoMaterial.objects.filter(apoyo__proyecto=proyecto)
        .values("material_id")
        .annotate(total=Sum("cantidad_requerida"))
    )
    inst_map = {item["material_id"]: item["total"] for item in apoyo_inst_qs}

    # 2. Materiales Requeridos directos del Proyecto (MaterialRequeridoProyecto)
    mat_req_extra = (
        MaterialRequeridoProyecto.objects.filter(proyecto=proyecto)
        .values("material_id")
        .annotate(total=Sum("cantidad_requerida"))
    )
    req_directo_map = {item["material_id"]: item["total"] for item in mat_req_extra}

    # Mapa consolidado de requeridos
    req_map = {}
    for m_id, cant in req_directo_map.items():
        req_map[m_id] = cant
    for m_id, cant in inst_map.items():
        if m_id not in req_map:
            req_map[m_id] = cant

    # 3. Entradas Suministradas (compras de proveedor o despachos de bodega)
    ent_qs = (
        DetalleEntradaMaterial.objects.filter(entrada__proyecto=proyecto)
        .values("material_id")
        .annotate(total=Sum("cantidad"))
    )
    ent_map = {item["material_id"]: item["total"] for item in ent_qs}

    # 4. Retiros / Desmontes del proyecto (desde los apoyos/postes)
    ret_qs = (
        ApoyoMaterial.objects.filter(apoyo__proyecto=proyecto)
        .values("material_id")
        .annotate(total=Sum("cantidad_retirada"))
    )
    ret_map = {item["material_id"]: item["total"] for item in ret_qs if item["total"] > 0}

    # 5. Obtener todos los materiales involucrados en el proyecto
    all_material_ids = set(req_map.keys()) | set(inst_map.keys()) | set(ent_map.keys()) | set(ret_map.keys())
    materiales_db = Material.objects.filter(id__in=all_material_ids).select_related("inventario").order_by("item", "descripcion")

    balance_materiales = []
    total_items_requeridos = Decimal("0")
    total_items_instalados = Decimal("0")
    total_items_entrados = Decimal("0")
    total_items_retirados = Decimal("0")
    total_devolucion = Decimal("0")

    for mat in materiales_db:
        sum_req = req_map.get(mat.id, Decimal("0"))
        sum_inst = inst_map.get(mat.id, Decimal("0"))
        sum_ent = ent_map.get(mat.id, Decimal("0"))
        sum_ret = ret_map.get(mat.id, Decimal("0"))
        devolucion = max(Decimal("0"), sum_ent - sum_inst)
        stock_bodega = getattr(mat, "inventario", None)
        stock_disponible = stock_bodega.cantidad if stock_bodega else Decimal("0")

        balance_materiales.append({
            "material": mat,
            "requerido": sum_req,
            "instalado": sum_inst,
            "stock_bodega": stock_disponible,
            "entrada": sum_ent,
            "retirado": sum_ret,
            "material_sobrante": sum_ent - sum_inst,
            "devolucion": devolucion,
        })

        total_items_requeridos += sum_req
        total_items_instalados += sum_inst
        total_items_entrados += sum_ent
        total_items_retirados += sum_ret
        total_devolucion += devolucion

    total_material_sobrante = total_items_entrados - total_items_instalados
    materiales_devolucion = [item for item in balance_materiales if item["devolucion"] > 0]

    entradas = (
        EntradaMaterialProyecto.objects.filter(proyecto=proyecto)
        .prefetch_related("detalles__material")
        .order_by("-fecha", "-id")
    )

    requeridos_proyecto = (
        MaterialRequeridoProyecto.objects.filter(proyecto=proyecto)
        .select_related("material")
        .order_by("material__descripcion")
    )

    instalados_apoyo = (
        ApoyoMaterial.objects.filter(apoyo__proyecto=proyecto, cantidad_requerida__gt=0)
        .select_related("apoyo", "material")
        .order_by("apoyo__numero_apoyo", "material__descripcion")
    )

    retiros_apoyo = (
        ApoyoMaterial.objects.filter(apoyo__proyecto=proyecto, cantidad_retirada__gt=0)
        .select_related("apoyo", "material")
        .order_by("apoyo__numero_apoyo", "material__descripcion")
    )

    materiales_catalogo = Material.objects.all().order_by("descripcion")

    return render(
        request,
        "logistica/proyectos/detalle_proyecto.html",
        {
            "proyecto": proyecto,
            "balance_materiales": balance_materiales,
            "materiales_devolucion": materiales_devolucion,
            "entradas": entradas,
            "requeridos_proyecto": requeridos_proyecto,
            "instalados_apoyo": instalados_apoyo,
            "retiros_apoyo": retiros_apoyo,
            "materiales_catalogo": materiales_catalogo,
            "total_items_requeridos": total_items_requeridos,
            "total_items_instalados": total_items_instalados,
            "total_items_entrados": total_items_entrados,
            "total_items_retirados": total_items_retirados,
            "total_material_sobrante": total_material_sobrante,
            "total_devolucion": total_devolucion,
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
    Genera y descarga un archivo Excel (.xlsx) de 1 sola hoja con la
    Matriz de Balance y Liquidación esencial de materiales del proyecto.
    """
    proyecto = get_object_or_404(Proyecto.objects.select_related("macroproyecto"), id=proyecto_id)

    # 1. Instalado en Apoyos (Ingeniería)
    apoyo_inst_qs = (
        ApoyoMaterial.objects.filter(apoyo__proyecto=proyecto)
        .values("material_id")
        .annotate(total=Sum("cantidad_requerida"))
    )
    inst_map = {item["material_id"]: item["total"] for item in apoyo_inst_qs}

    # 2. Materiales Requeridos directos del Proyecto
    mat_req_extra = (
        MaterialRequeridoProyecto.objects.filter(proyecto=proyecto)
        .values("material_id")
        .annotate(total=Sum("cantidad_requerida"))
    )
    req_directo_map = {item["material_id"]: item["total"] for item in mat_req_extra}

    # Consolidar mapa de requeridos
    req_map = {}
    for m_id, cant in req_directo_map.items():
        req_map[m_id] = cant
    for m_id, cant in inst_map.items():
        if m_id not in req_map:
            req_map[m_id] = cant

    # 3. Entradas Suministradas (EntradaMaterialProyecto)
    ent_qs = (
        DetalleEntradaMaterial.objects.filter(entrada__proyecto=proyecto)
        .values("material_id")
        .annotate(total=Sum("cantidad"))
    )
    ent_map = {item["material_id"]: item["total"] for item in ent_qs}

    # 4. Retiros / Desmontes del proyecto (desde ApoyoMaterial)
    ret_qs = (
        ApoyoMaterial.objects.filter(apoyo__proyecto=proyecto)
        .values("material_id")
        .annotate(total=Sum("cantidad_retirada"))
    )
    ret_map = {item["material_id"]: item["total"] for item in ret_qs if item["total"] > 0}

    # 5. Materiales involucrados
    all_material_ids = set(req_map.keys()) | set(inst_map.keys()) | set(ent_map.keys()) | set(ret_map.keys())
    materiales_db = list(Material.objects.filter(id__in=all_material_ids).select_related("inventario").order_by("item", "descripcion"))

    wb = openpyxl.Workbook()
    ws1 = wb.active
    ws1.title = "Balance de Materiales"

    font_titulo = Font(name="Calibri", size=13, bold=True, color="1E3A8A")
    font_subtitulo = Font(name="Calibri", size=10, bold=True, color="4B5563")
    font_header = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    font_data = Font(name="Calibri", size=10, color="111827")
    font_total = Font(name="Calibri", size=10, bold=True, color="1E3A8A")

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

    def fmt_v(v):
        if v is None:
            return 0
        return int(v) if v % 1 == 0 else float(v)

    macro_nom = proyecto.macroproyecto.nombre if proyecto.macroproyecto else "Sin Macroproyecto"
    fecha_hoy = timezone.now().strftime('%d/%m/%Y')

    # ENCABEZADO INSTITUCIONAL
    ws1.merge_cells("A1:I1")
    ws1["A1"] = f"COINTECA S.A.S. — MATRIZ DE BALANCE Y LIQUIDACIÓN (PROYECTO {proyecto.numero_emcali})"
    ws1["A1"].font = font_titulo
    ws1["A1"].alignment = align_left

    ws1.merge_cells("A2:I2")
    ws1["A2"] = f"PROYECTO: {proyecto.numero_emcali}  |  TIPO: {proyecto.tipo}  |  ESTADO: {proyecto.estado}  |  MACROPROYECTO: {macro_nom}  |  FECHA: {fecha_hoy}"
    ws1["A2"].font = font_subtitulo
    ws1["A2"].alignment = align_left

    ws1.append([])
    headers1 = [
        "ÍTEM",
        "DESCRIPCIÓN DEL MATERIAL",
        "UNIDAD",
        "MATERIALES REQUERIDOS",
        "SUMINISTRADO (ENTRADAS)",
        "MATERIALES INSTALADOS",
        "MATERIALES RETIRADOS",
        "MATERIAL DE DEVOLUCIÓN (SOBRANTE)",
        "STOCK EN BODEGA",
    ]
    ws1.append(headers1)

    for col in range(1, 10):
        c = ws1.cell(row=4, column=col)
        c.font = font_header
        c.fill = fill_header
        c.alignment = align_center if col not in [2] else align_left
        c.border = border_cell

    row_idx = 5
    tot_req = Decimal("0")
    tot_ent = Decimal("0")
    tot_inst = Decimal("0")
    tot_ret = Decimal("0")
    tot_dev = Decimal("0")

    for idx, mat in enumerate(materiales_db, start=1):
        c_req = req_map.get(mat.id, Decimal("0"))
        c_ent = ent_map.get(mat.id, Decimal("0"))
        c_inst = inst_map.get(mat.id, Decimal("0"))
        c_ret = ret_map.get(mat.id, Decimal("0"))
        c_dev = max(Decimal("0"), c_ent - c_inst)
        stock_obj = getattr(mat, "inventario", None)
        c_stock = stock_obj.cantidad if stock_obj else Decimal("0")

        tot_req += c_req
        tot_ent += c_ent
        tot_inst += c_inst
        tot_ret += c_ret
        tot_dev += c_dev

        ws1.append([
            mat.item or "",
            mat.descripcion,
            mat.unidad or "UN",
            fmt_v(c_req),
            fmt_v(c_ent),
            fmt_v(c_inst),
            fmt_v(c_ret),
            fmt_v(c_dev),
            fmt_v(c_stock),
        ])

        for col in range(1, 10):
            c = ws1.cell(row=row_idx, column=col)
            c.font = font_data
            c.border = border_cell
            if idx % 2 == 0:
                c.fill = fill_zebra
            if col in [1, 3]:
                c.alignment = align_center
            elif col == 2:
                c.alignment = align_left
            else:
                c.alignment = align_right
                c.number_format = "#,##0" if isinstance(c.value, int) else "0.##"
        row_idx += 1

    # Fila de Totales
    ws1.append([
        "",
        "TOTALES CONSOLIDADOS",
        f"{len(materiales_db)} ÍTEMS",
        fmt_v(tot_req),
        fmt_v(tot_ent),
        fmt_v(tot_inst),
        fmt_v(tot_ret),
        fmt_v(tot_dev),
        "—"
    ])
    for col in range(1, 10):
        c = ws1.cell(row=row_idx, column=col)
        c.font = font_total
        c.fill = fill_total
        c.border = border_total
        if col in [1, 3, 9]:
            c.alignment = align_center
        elif col == 2:
            c.alignment = align_left
        else:
            c.alignment = align_right
            c.number_format = "#,##0" if isinstance(c.value, int) else "0.##"

    ws1.column_dimensions["A"].width = 12
    ws1.column_dimensions["B"].width = 46
    ws1.column_dimensions["C"].width = 12
    ws1.column_dimensions["D"].width = 22
    ws1.column_dimensions["E"].width = 24
    ws1.column_dimensions["F"].width = 22
    ws1.column_dimensions["G"].width = 22
    ws1.column_dimensions["H"].width = 26
    ws1.column_dimensions["I"].width = 18

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    filename = f"Balance_Materiales_Proyecto_{proyecto.numero_emcali}.xlsx"
    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


# ==============================================================================
# INFORME CONSOLIDADO MULTI-PROYECTO Y GESTIÓN DE RETIROS DE MATERIALES
# ==============================================================================

@login_required
def informe_consolidado_proyectos(request):
    """
    Informe Consolidado Multi-Proyecto (Liquidación de Obras).
    Permite seleccionar múltiples proyectos marcados con checkboxes y consolidar:
    - Entradas Suministradas a obra
    - Material Instalado en Apoyos
    - Material Retirado / Desmontado (en BT y AP)
    - Saldo final de Liquidación
    """
    proyecto_ids = (
        request.GET.getlist("proyectos")
        or request.GET.getlist("proyectos[]")
        or request.POST.getlist("proyectos")
        or request.POST.getlist("proyectos[]")
    )

    if not proyecto_ids:
        raw_ids = request.GET.get("ids", "") or request.POST.get("ids", "")
        if raw_ids:
            proyecto_ids = [x.strip() for x in raw_ids.split(",") if x.strip()]

    if not proyecto_ids:
        return redirect("proyectos_logistica")

    proyectos_seleccionados = Proyecto.objects.filter(id__in=proyecto_ids).order_by("numero_emcali")

    if not proyectos_seleccionados.exists():
        return redirect("proyectos_logistica")

    # 1. Consolidar Entradas
    ent_qs = (
        DetalleEntradaMaterial.objects.filter(entrada__proyecto__in=proyectos_seleccionados)
        .values("material_id")
        .annotate(total=Sum("cantidad"))
    )
    ent_map = {item["material_id"]: item["total"] for item in ent_qs}

    # 2. Consolidar Instalado en Apoyos (Ingeniería)
    inst_qs = (
        ApoyoMaterial.objects.filter(apoyo__proyecto__in=proyectos_seleccionados)
        .values("material_id")
        .annotate(total=Sum("cantidad_requerida"))
    )
    inst_map = {item["material_id"]: item["total"] for item in inst_qs}

    # 3. Consolidar Retiros / Desmontes (desde los apoyos de ingeniería)
    ret_qs = (
        ApoyoMaterial.objects.filter(apoyo__proyecto__in=proyectos_seleccionados)
        .values("material_id")
        .annotate(total=Sum("cantidad_retirada"))
    )
    ret_map = {item["material_id"]: item["total"] for item in ret_qs if item["total"] > 0}

    # 4. Consolidar Requerimientos generales
    req_qs = (
        MaterialRequeridoProyecto.objects.filter(proyecto__in=proyectos_seleccionados)
        .values("material_id")
        .annotate(total=Sum("cantidad_requerida"))
    )
    req_map = {item["material_id"]: item["total"] for item in req_qs}

    # 5. Todos los materiales involucrados
    all_mat_ids = set(ent_map.keys()) | set(inst_map.keys()) | set(ret_map.keys()) | set(req_map.keys())
    materiales_db = Material.objects.filter(id__in=all_mat_ids).select_related("inventario").order_by("item", "descripcion")

    tabla_consolidada = []
    total_entrado_general = Decimal("0")
    total_instalado_general = Decimal("0")
    total_retirado_general = Decimal("0")
    total_requerido_general = Decimal("0")
    total_devolucion_general = Decimal("0")

    for mat in materiales_db:
        cant_ent = ent_map.get(mat.id, Decimal("0"))
        cant_inst = inst_map.get(mat.id, Decimal("0"))
        cant_ret = ret_map.get(mat.id, Decimal("0"))
        cant_req = req_map.get(mat.id, Decimal("0"))
        saldo = cant_ent - cant_inst
        devolucion = max(Decimal("0"), cant_ent - cant_inst)

        stock_bodega = getattr(mat, "inventario", None)
        stock_disponible = stock_bodega.cantidad if stock_bodega else Decimal("0")

        tabla_consolidada.append({
            "material": mat,
            "entrado": cant_ent,
            "instalado": cant_inst,
            "retirado": cant_ret,
            "requerido": cant_req,
            "saldo": saldo,
            "devolucion": devolucion,
            "stock_bodega": stock_disponible,
        })

        total_entrado_general += cant_ent
        total_instalado_general += cant_inst
        total_retirado_general += cant_ret
        total_requerido_general += cant_req
        total_devolucion_general += devolucion

    # 6. Desglose individual de cada proyecto seleccionado
    desglose_proyectos = []
    for p in proyectos_seleccionados:
        p_ent_qs = DetalleEntradaMaterial.objects.filter(entrada__proyecto=p).values("material_id").annotate(total=Sum("cantidad"))
        p_ent_map = {x["material_id"]: x["total"] for x in p_ent_qs}

        p_inst_qs = ApoyoMaterial.objects.filter(apoyo__proyecto=p).values("material_id").annotate(total=Sum("cantidad_requerida"))
        p_inst_map = {x["material_id"]: x["total"] for x in p_inst_qs}

        p_ret_qs = ApoyoMaterial.objects.filter(apoyo__proyecto=p).values("material_id").annotate(total=Sum("cantidad_retirada"))
        p_ret_map = {x["material_id"]: x["total"] for x in p_ret_qs if x["total"] > 0}

        p_mat_ids = set(p_ent_map.keys()) | set(p_inst_map.keys()) | set(p_ret_map.keys())
        p_materiales = Material.objects.filter(id__in=p_mat_ids).order_by("descripcion")

        items_proyecto = []
        p_tot_ent = Decimal("0")
        p_tot_inst = Decimal("0")
        p_tot_ret = Decimal("0")
        p_tot_dev = Decimal("0")

        for mat in p_materiales:
            c_ent = p_ent_map.get(mat.id, Decimal("0"))
            c_inst = p_inst_map.get(mat.id, Decimal("0"))
            c_ret = p_ret_map.get(mat.id, Decimal("0"))
            c_dev = max(Decimal("0"), c_ent - c_inst)
            items_proyecto.append({
                "material": mat,
                "entrado": c_ent,
                "instalado": c_inst,
                "retirado": c_ret,
                "saldo": c_ent - c_inst,
                "devolucion": c_dev,
            })
            p_tot_ent += c_ent
            p_tot_inst += c_inst
            p_tot_ret += c_ret
            p_tot_dev += c_dev

        desglose_proyectos.append({
            "proyecto": p,
            "items": items_proyecto,
            "total_entrado": p_tot_ent,
            "total_instalado": p_tot_inst,
            "total_retirado": p_tot_ret,
            "total_devolucion": p_tot_dev,
            "saldo_proyecto": p_tot_ent - p_tot_inst,
            "num_entradas": p.entradas_material.count(),
            "num_apoyos": p.apoyos.count(),
            "num_retiros": ApoyoMaterial.objects.filter(apoyo__proyecto=p, cantidad_retirada__gt=0).count(),
        })

    ids_string = ",".join(str(p.id) for p in proyectos_seleccionados)

    return render(
        request,
        "logistica/proyectos/informe_consolidado.html",
        {
            "proyectos_seleccionados": proyectos_seleccionados,
            "total_proyectos_sel": proyectos_seleccionados.count(),
            "tabla_consolidada": tabla_consolidada,
            "total_entrado_general": total_entrado_general,
            "total_instalado_general": total_instalado_general,
            "total_retirado_general": total_retirado_general,
            "total_requerido_general": total_requerido_general,
            "total_devolucion_general": total_devolucion_general,
            "saldo_total_general": total_entrado_general - total_instalado_general,
            "desglose_proyectos": desglose_proyectos,
            "ids_string": ids_string,
        }
    )


@login_required
def exportar_informe_consolidado_excel(request):
    """
    Descarga el informe consolidado multi-proyecto en formato Excel (.xlsx) con:
    - Hoja 1: "Consolidado Obras" (Entradas, Instalado, Retiros, Sobrantes y Stock en Bodega)
    - Hoja 2: "Devolución a Bodega" (Materiales sobrantes para reintegro a bodega)
    """
    raw_ids = request.GET.get("ids", "") or request.POST.get("ids", "")
    if not raw_ids:
        proyecto_ids = request.GET.getlist("proyectos") or request.GET.getlist("proyectos[]")
    else:
        proyecto_ids = [x.strip() for x in raw_ids.split(",") if x.strip()]

    proyectos_seleccionados = Proyecto.objects.filter(id__in=proyecto_ids).order_by("numero_emcali")
    if not proyectos_seleccionados.exists():
        return redirect("proyectos_logistica")

    ent_qs = DetalleEntradaMaterial.objects.filter(entrada__proyecto__in=proyectos_seleccionados).values("material_id").annotate(total=Sum("cantidad"))
    ent_map = {item["material_id"]: item["total"] for item in ent_qs}

    inst_qs = ApoyoMaterial.objects.filter(apoyo__proyecto__in=proyectos_seleccionados).values("material_id").annotate(total=Sum("cantidad_requerida"))
    inst_map = {item["material_id"]: item["total"] for item in inst_qs}

    ret_qs = ApoyoMaterial.objects.filter(apoyo__proyecto__in=proyectos_seleccionados).values("material_id").annotate(total=Sum("cantidad_retirada"))
    ret_map = {item["material_id"]: item["total"] for item in ret_qs if item["total"] > 0}

    all_mat_ids = set(ent_map.keys()) | set(inst_map.keys()) | set(ret_map.keys())
    materiales_db = Material.objects.filter(id__in=all_mat_ids).select_related("inventario").order_by("item", "descripcion")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Consolidado Obras"

    font_titulo = Font(name="Calibri", size=13, bold=True, color="1E3A8A")
    font_subtitulo = Font(name="Calibri", size=10, bold=True, color="4B5563")
    font_header = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    font_data = Font(name="Calibri", size=10, color="111827")
    font_total = Font(name="Calibri", size=10, bold=True, color="1E3A8A")

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

    proyectos_nombres = ", ".join(p.numero_emcali for p in proyectos_seleccionados)
    fecha_hoy = timezone.now().strftime('%d/%m/%Y')

    ws.merge_cells("A1:H1")
    ws["A1"] = "COINTECA S.A.S. — INFORME CONSOLIDADO DE MATERIALES Y RETIROS"
    ws["A1"].font = font_titulo
    ws["A1"].alignment = align_left

    ws.merge_cells("A2:H2")
    ws["A2"] = f"PROYECTOS CONSOLIDADOS ({proyectos_seleccionados.count()}): {proyectos_nombres}  |  FECHA: {fecha_hoy}"
    ws["A2"].font = font_subtitulo
    ws["A2"].alignment = align_left

    ws.append([])

    headers = [
        "ÍTEM",
        "DESCRIPCIÓN DEL MATERIAL",
        "UNIDAD",
        "ENTRADA (SUMINISTRADO)",
        "INSTALADO EN POSTES",
        "RETIRO / DESMONTE",
        "MATERIAL DE DEVOLUCIÓN (SOBRANTE)",
        "STOCK EN BODEGA"
    ]
    ws.append(headers)
    header_row = 4

    for col_idx in range(1, 9):
        cell = ws.cell(row=header_row, column=col_idx)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = align_center if col_idx != 2 else align_left
        cell.border = border_cell

    current_row = header_row + 1
    tot_ent = Decimal("0")
    tot_inst = Decimal("0")
    tot_ret = Decimal("0")
    tot_dev = Decimal("0")

    materiales_devolucion = []

    def fmt_val(v):
        if v is None:
            return 0
        return int(v) if v % 1 == 0 else float(v)

    for idx, mat in enumerate(materiales_db, start=1):
        c_ent = ent_map.get(mat.id, Decimal("0"))
        c_inst = inst_map.get(mat.id, Decimal("0"))
        c_ret = ret_map.get(mat.id, Decimal("0"))
        c_dev = max(Decimal("0"), c_ent - c_inst)
        stock_obj = getattr(mat, "inventario", None)
        c_stock = stock_obj.cantidad if stock_obj else Decimal("0")

        tot_ent += c_ent
        tot_inst += c_inst
        tot_ret += c_ret
        tot_dev += c_dev

        if c_dev > 0:
            materiales_devolucion.append({
                "mat": mat,
                "ent": c_ent,
                "inst": c_inst,
                "dev": c_dev,
                "stock": c_stock
            })

        ws.append([
            mat.item or "",
            mat.descripcion,
            mat.unidad or "UN",
            fmt_val(c_ent),
            fmt_val(c_inst),
            fmt_val(c_ret),
            fmt_val(c_dev),
            fmt_val(c_stock)
        ])

        for col_idx in range(1, 9):
            c = ws.cell(row=current_row, column=col_idx)
            c.font = font_data
            c.border = border_cell
            if idx % 2 == 0:
                c.fill = fill_zebra

            if col_idx in [1, 3]:
                c.alignment = align_center
            elif col_idx == 2:
                c.alignment = align_left
            else:
                c.alignment = align_right
                c.number_format = "#,##0" if isinstance(c.value, int) else "0.##"

        current_row += 1

    ws.append([
        "",
        "TOTALES CONSOLIDADOS",
        f"{len(materiales_db)} ÍTEMS",
        fmt_val(tot_ent),
        fmt_val(tot_inst),
        fmt_val(tot_ret),
        fmt_val(tot_dev),
        "—"
    ])
    for col_idx in range(1, 9):
        c = ws.cell(row=current_row, column=col_idx)
        c.font = font_total
        c.fill = fill_total
        c.border = border_total
        if col_idx in [1, 3, 8]:
            c.alignment = align_center
        elif col_idx == 2:
            c.alignment = align_left
        else:
            c.alignment = align_right
            c.number_format = "#,##0" if isinstance(c.value, int) else "0.##"

    ws.column_dimensions["A"].width = 12
    ws.column_dimensions["B"].width = 46
    ws.column_dimensions["C"].width = 12
    ws.column_dimensions["D"].width = 24
    ws.column_dimensions["E"].width = 22
    ws.column_dimensions["F"].width = 22
    ws.column_dimensions["G"].width = 26
    ws.column_dimensions["H"].width = 18

    # HOJA 2: DEVOLUCIÓN A BODEGA (REINTEGROS)
    if materiales_devolucion:
        ws_dev = wb.create_sheet(title="Devolución a Bodega")
        ws_dev.merge_cells("A1:G1")
        ws_dev["A1"] = f"COINTECA S.A.S. — MATERIALES DE DEVOLUCIÓN A BODEGA (CONSOLIDADO)"
        ws_dev["A1"].font = font_titulo
        ws_dev["A1"].alignment = align_left

        ws_dev.merge_cells("A2:G2")
        ws_dev["A2"] = f"MATERIALES SOBRANTES CONSOLIDADOS TRAS INSTALACIÓN  |  FECHA: {fecha_hoy}"
        ws_dev_headers = [
            "ÍTEM",
            "DESCRIPCIÓN DEL MATERIAL",
            "UNIDAD",
            "SUMINISTRADO (ENTRADAS)",
            "INSTALADO EN POSTES",
            "CANTIDAD A DEVOLVER / REINTEGRAR",
            "STOCK ACTUAL EN BODEGA"
        ]
        ws_dev.append([])
        ws_dev.append(ws_dev_headers)

        for col in range(1, 8):
            c = ws_dev.cell(row=4, column=col)
            c.font = font_header
            c.fill = fill_header
            c.alignment = align_center if col != 2 else align_left
            c.border = border_cell

        row_dev_idx = 5
        tot_d_ent = Decimal("0")
        tot_d_inst = Decimal("0")
        tot_d_dev = Decimal("0")

        for idx, d in enumerate(materiales_devolucion, start=1):
            tot_d_ent += d["ent"]
            tot_d_inst += d["inst"]
            tot_d_dev += d["dev"]

            ws_dev.append([
                d["mat"].item or "",
                d["mat"].descripcion,
                d["mat"].unidad or "UN",
                fmt_val(d["ent"]),
                fmt_val(d["inst"]),
                fmt_val(d["dev"]),
                fmt_val(d["stock"])
            ])

            for col in range(1, 8):
                c = ws_dev.cell(row=row_dev_idx, column=col)
                c.font = font_data
                c.border = border_cell
                if idx % 2 == 0:
                    c.fill = fill_zebra
                if col in [1, 3]:
                    c.alignment = align_center
                elif col == 2:
                    c.alignment = align_left
                else:
                    c.alignment = align_right
                    c.number_format = "#,##0" if isinstance(c.value, int) else "0.##"
            row_dev_idx += 1

        ws_dev.append([
            "",
            "TOTAL A DEVOLVER A BODEGA",
            f"{len(materiales_devolucion)} ÍTEMS",
            fmt_val(tot_d_ent),
            fmt_val(tot_d_inst),
            fmt_val(tot_d_dev),
            "—"
        ])
        for col in range(1, 8):
            c = ws_dev.cell(row=row_dev_idx, column=col)
            c.font = font_total
            c.fill = fill_total
            c.border = border_total
            if col in [1, 3, 7]:
                c.alignment = align_center
            elif col == 2:
                c.alignment = align_left
            else:
                c.alignment = align_right
                c.number_format = "#,##0" if isinstance(c.value, int) else "0.##"

        ws_dev.column_dimensions["A"].width = 12
        ws_dev.column_dimensions["B"].width = 48
        ws_dev.column_dimensions["C"].width = 12
        ws_dev.column_dimensions["D"].width = 24
        ws_dev.column_dimensions["E"].width = 22
        ws_dev.column_dimensions["F"].width = 28
        ws_dev.column_dimensions["G"].width = 20

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    filename = f"Informe_Consolidado_Proyectos_{timezone.now().strftime('%Y%m%d_%H%M')}.xlsx"
    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


# ==============================================================================
# GESTIÓN DE RETIROS / DESMONTES DE MATERIALES POR PROYECTO
# ==============================================================================

@login_required
@transaction.atomic
def registrar_retiro_material(request, proyecto_id):
    """
    Registra actas/planillas de materiales desmontados o retirados en la obra.
    """
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    materiales = Material.objects.all().order_by("descripcion")

    retiros = (
        RetiroMaterialProyecto.objects.filter(proyecto=proyecto)
        .prefetch_related("detalles__material")
        .order_by("-fecha", "-id")
    )

    if request.method == "POST":
        fecha = request.POST.get("fecha")
        if fecha:
            retiro = RetiroMaterialProyecto.objects.create(
                proyecto=proyecto,
                fecha=fecha,
                responsable=request.POST.get("responsable", "").strip(),
                numero_acta=request.POST.get("numero_acta", "").strip(),
                observaciones=request.POST.get("observaciones", "").strip(),
            )

            material_ids = request.POST.getlist("material_id[]")
            cantidades = request.POST.getlist("cantidad[]")
            estados = request.POST.getlist("estado_material[]")

            detalles = []
            for i, (mat_id, cant_str) in enumerate(zip(material_ids, cantidades)):
                if not mat_id or not cant_str:
                    continue
                try:
                    cant = Decimal(str(cant_str).strip())
                    if cant > 0:
                        est = estados[i] if i < len(estados) and estados[i] else "Bueno"
                        detalles.append(
                            DetalleRetiroMaterial(
                                retiro=retiro,
                                material_id=mat_id,
                                cantidad=cant,
                                estado_material=est
                            )
                        )
                except (ValueError, TypeError, Decimal.InvalidOperation):
                    continue

            if detalles:
                DetalleRetiroMaterial.objects.bulk_create(detalles)

            return redirect("registrar_retiro_material", proyecto_id=proyecto.id)

    return render(
        request,
        "logistica/proyectos/crear_retiro.html",
        {
            "proyecto": proyecto,
            "materiales": materiales,
            "retiros": retiros,
        }
    )


@login_required
@transaction.atomic
def eliminar_retiro_material(request, retiro_id):
    """
    Elimina un registro de retiro/desmonte de material.
    """
    retiro = get_object_or_404(RetiroMaterialProyecto, id=retiro_id)
    proyecto_id = retiro.proyecto.id
    if request.method == "POST":
        retiro.delete()
    return redirect("registrar_retiro_material", proyecto_id=proyecto_id)


# ==============================================================================
# VISTA GLOBAL DE MATERIALES EN LOGÍSTICA (KARDEX EDSON + MATRIZ DE NODOS)
# ==============================================================================

@login_required
def vista_global_logistica(request, macroproyecto_id=None, proyecto_id=None):
    """
    Vista Global y Consolidada de Materiales en Logística.
    Permite navegar fluidamente entre cualquier Macroproyecto y Proyecto (ej: Proyecto 9901)
    o ver el consolidado de todos los proyectos de un macroproyecto / globales, visualizando:
    1. Selector interactivo superior de Macroproyecto y Proyecto con opción multi-proyecto / consolidado.
    2. Tabla Matriz Completa de Nodos / Apoyos con datos técnicos (fecha, dirección/barrio, tipo instalación, tipo estructura, retenidas, materiales instalados y retirados, luminarias, estado).
    3. Motor de filtros interactivos tipo Excel (orden A-Z, buscador, selección múltiple de casillas).
    4. Matriz de Liquidación y Balance con columna 'Material que Sobra' (Suministrado - Instalado).
    5. Resumen de retiros / desmontes y remisiones de entrada.
    6. Indicador contextual de tipo de red y maniobras EMCALI/COINTECA.
    """
    todos_macroproyectos = Macroproyecto.objects.all().order_by("nombre")
    todos_proyectos_raw = Proyecto.objects.select_related("macroproyecto").order_by("numero_emcali")

    proyectos_js = []
    for p in todos_proyectos_raw:
        proyectos_js.append({
            "id": p.id,
            "numero": p.numero_emcali,
            "macro_id": p.macroproyecto_id or "",
            "macro_nombre": p.macroproyecto.nombre if p.macroproyecto else "Sin Macroproyecto",
            "tipo": p.tipo,
            "tipo_display": p.get_tipo_display() if hasattr(p, 'get_tipo_display') else p.tipo,
            "estado": p.estado,
        })

    macro_id_param = request.GET.get("macroproyecto_id") or macroproyecto_id
    proy_id_param = request.GET.get("proyecto_id") or proyecto_id
    tipo_filtro = request.GET.get("tipo", "").strip()
    query = request.GET.get("q", "").strip()

    macro_seleccionado = None
    if macro_id_param and str(macro_id_param).isdigit():
        macro_seleccionado = Macroproyecto.objects.filter(id=int(macro_id_param)).first()

    proyecto_seleccionado = None
    es_consolidado = False

    if proy_id_param and str(proy_id_param).isdigit():
        proyecto_seleccionado = Proyecto.objects.filter(id=int(proy_id_param)).select_related("macroproyecto").first()
        if proyecto_seleccionado:
            proyectos_scope = Proyecto.objects.filter(id=proyecto_seleccionado.id).select_related("macroproyecto")
            if not macro_seleccionado and proyecto_seleccionado.macroproyecto:
                macro_seleccionado = proyecto_seleccionado.macroproyecto
        else:
            proyectos_scope = Proyecto.objects.none()
    elif proy_id_param == "todos":
        es_consolidado = True
        if macro_seleccionado:
            proyectos_scope = Proyecto.objects.filter(macroproyecto=macro_seleccionado).select_related("macroproyecto").order_by("numero_emcali")
        else:
            proyectos_scope = Proyecto.objects.all().select_related("macroproyecto").order_by("numero_emcali")
    elif macro_seleccionado:
        # Por defecto si se selecciona un macroproyecto y no se especifica proyecto, mostrar el consolidado del macro
        proyectos_scope = Proyecto.objects.filter(macroproyecto=macro_seleccionado).select_related("macroproyecto").order_by("numero_emcali")
        if proyectos_scope.count() == 1:
            proyecto_seleccionado = proyectos_scope.first()
        else:
            es_consolidado = True
    elif todos_proyectos_raw.exists():
        proyecto_seleccionado = todos_proyectos_raw.first()
        proyectos_scope = Proyecto.objects.filter(id=proyecto_seleccionado.id).select_related("macroproyecto")
        if proyecto_seleccionado.macroproyecto:
            macro_seleccionado = proyecto_seleccionado.macroproyecto
    else:
        proyectos_scope = Proyecto.objects.none()

    filas_matriz = []
    materiales_columnas = []
    fila_totales = []
    tabla_resumen_retiros = []
    apoyos = []
    balance_materiales = []
    entradas = []
    retiros_actas = []

    total_items_requeridos = Decimal("0")
    total_items_instalados = Decimal("0")
    total_items_entrados = Decimal("0")
    total_items_retirados = Decimal("0")
    total_material_sobrante = Decimal("0")
    nota_tecnica_red = ""

    materiales_devolucion = []
    total_devolucion = Decimal("0")

    if proyectos_scope.exists():
        if proyecto_seleccionado:
            p = proyecto_seleccionado
            if p.tipo == "MT":
                nota_tecnica_red = "⚡ En Media Tensión (MT) no se realizan desmontes ni retiros de luminarias. Se audita exclusivamente el suministro e instalación técnica en red primaria."
            elif p.tipo in ["AP_BARRIO", "AP_PARQUE", "AP"]:
                nota_tecnica_red = "💡 En Alumbrado Público (AP) se audita la instalación de nuevas luminarias y materiales, así como los desmontes y retiros de luminarias y equipos antiguos."
            elif p.tipo == "BT":
                nota_tecnica_red = "🔌 En Baja Tensión (BT) se audita el tendido de red, postes técnicos, accesorios y retiros aplicables."
            else:
                nota_tecnica_red = "🔧 Control y conciliación de materiales en obra."
        else:
            nota_tecnica_red = f"🌐 Visualización consolidada de {proyectos_scope.count()} proyecto(s). Usa los filtros tipo Excel en cada columna para segmentar por barrio, tipo de instalación, cuadrilla o fecha con exactitud."

        # A. Apoyos y Matriz Poste a Poste (Formato Ingeniería con datos técnicos completos)
        apoyos = (
            Apoyo.objects
            .filter(proyecto__in=proyectos_scope)
            .select_related("quien_ejecuta", "proyecto", "proyecto__macroproyecto")
            .prefetch_related("luminarias")
            .order_by("proyecto__numero_emcali", "numero_apoyo", "id")
        )

        apoyo_materiales = ApoyoMaterial.objects.filter(
            apoyo__proyecto__in=proyectos_scope
        ).select_related("material")

        materiales_ids = apoyo_materiales.values_list('material_id', flat=True).distinct()
        materiales_columnas = list(Material.objects.filter(id__in=materiales_ids).order_by("item", "descripcion"))

        cantidades_inst_map = {}
        cantidades_ret_map = {}
        for am in apoyo_materiales:
            cantidades_inst_map[(am.apoyo_id, am.material_id)] = am.cantidad_requerida
            cantidades_ret_map[(am.apoyo_id, am.material_id)] = am.cantidad_retirada

        totales_inst_columna = {mat.id: Decimal("0") for mat in materiales_columnas}
        totales_ret_columna = {mat.id: Decimal("0") for mat in materiales_columnas}

        for ap in apoyos:
            celdas = []
            for mat in materiales_columnas:
                cant_inst = cantidades_inst_map.get((ap.id, mat.id), Decimal("0"))
                cant_ret = cantidades_ret_map.get((ap.id, mat.id), Decimal("0"))
                celdas.append({
                    "material": mat,
                    "cantidad": cant_inst,
                    "cantidad_retirada": cant_ret,
                })
                totales_inst_columna[mat.id] += cant_inst
                totales_ret_columna[mat.id] += cant_ret

            filas_matriz.append({
                "apoyo": ap,
                "celdas": celdas,
            })

        for mat in materiales_columnas:
            fila_totales.append({
                "material": mat,
                "total": totales_inst_columna.get(mat.id, Decimal("0")),
                "total_retirado": totales_ret_columna.get(mat.id, Decimal("0")),
            })

        for mat in materiales_columnas:
            tot_ret = totales_ret_columna.get(mat.id, Decimal("0"))
            if tot_ret > 0:
                tabla_resumen_retiros.append({
                    "material": mat,
                    "cantidad_retirada": tot_ret,
                })

        # B. Matriz de Liquidación y Balance (Estilo Edson)
        inst_qs = (
            ApoyoMaterial.objects.filter(apoyo__proyecto__in=proyectos_scope)
            .values("material_id")
            .annotate(total=Sum("cantidad_requerida"))
        )
        inst_map = {item["material_id"]: item["total"] for item in inst_qs}

        req_qs = (
            MaterialRequeridoProyecto.objects.filter(proyecto__in=proyectos_scope)
            .values("material_id")
            .annotate(total=Sum("cantidad_requerida"))
        )
        req_map = {item["material_id"]: item["total"] for item in req_qs}
        for m_id, cant in inst_map.items():
            if m_id not in req_map:
                req_map[m_id] = cant

        ent_qs = (
            DetalleEntradaMaterial.objects.filter(entrada__proyecto__in=proyectos_scope)
            .values("material_id")
            .annotate(total=Sum("cantidad"))
        )
        ent_map = {item["material_id"]: item["total"] for item in ent_qs}

        ret_qs = (
            ApoyoMaterial.objects.filter(apoyo__proyecto__in=proyectos_scope)
            .values("material_id")
            .annotate(total=Sum("cantidad_retirada"))
        )
        ret_map = {item["material_id"]: item["total"] for item in ret_qs if item["total"] > 0}

        all_mat_ids = set(req_map.keys()) | set(inst_map.keys()) | set(ent_map.keys()) | set(ret_map.keys())
        materiales_db = Material.objects.filter(id__in=all_mat_ids).select_related("inventario").order_by("item", "descripcion")

        if query:
            materiales_db = materiales_db.filter(
                Q(descripcion__icontains=query) |
                Q(item__icontains=query)
            )

        for mat in materiales_db:
            sum_req = req_map.get(mat.id, Decimal("0"))
            sum_inst = inst_map.get(mat.id, Decimal("0"))
            sum_ent = ent_map.get(mat.id, Decimal("0"))
            sum_ret = ret_map.get(mat.id, Decimal("0"))
            material_sobrante = sum_ent - sum_inst
            stock_bodega = getattr(mat, "inventario", None)
            stock_disp = stock_bodega.cantidad if stock_bodega else Decimal("0")

            balance_materiales.append({
                "material": mat,
                "requerido": sum_req,
                "entrada": sum_ent,
                "instalado": sum_inst,
                "retirado": sum_ret,
                "material_sobrante": material_sobrante,
                "devolucion": material_sobrante if material_sobrante > 0 else Decimal("0"),
                "stock_bodega": stock_disp,
            })

            total_items_requeridos += sum_req
            total_items_instalados += sum_inst
            total_items_entrados += sum_ent
            total_items_retirados += sum_ret

        total_material_sobrante = total_items_entrados - total_items_instalados

        # C. Materiales con saldo sobrante que deben reintegrarse/devolverse a bodega
        materiales_devolucion = [item for item in balance_materiales if item["material_sobrante"] > 0]
        total_devolucion = sum(item["material_sobrante"] for item in materiales_devolucion)

        entradas = (
            EntradaMaterialProyecto.objects.filter(proyecto__in=proyectos_scope)
            .prefetch_related("detalles__material", "proyecto")
            .order_by("-fecha", "-id")
        )
        retiros_actas = (
            RetiroMaterialProyecto.objects.filter(proyecto__in=proyectos_scope)
            .prefetch_related("detalles__material", "proyecto")
            .order_by("-fecha", "-id")
        )

    maniobra_emcali_display = ""
    maniobra_cointeca_display = ""
    if macro_seleccionado:
        maniobra_emcali_display = macro_seleccionado.numero_maniobra_emcali or ""
        maniobra_cointeca_display = macro_seleccionado.numero_maniobra_cointeca or ""
    elif proyecto_seleccionado and proyecto_seleccionado.macroproyecto:
        maniobra_emcali_display = proyecto_seleccionado.macroproyecto.numero_maniobra_emcali or ""
        maniobra_cointeca_display = proyecto_seleccionado.macroproyecto.numero_maniobra_cointeca or ""

    proyectos_macro_list = []
    if macro_seleccionado:
        proyectos_macro_list = Proyecto.objects.filter(macroproyecto=macro_seleccionado).order_by("numero_emcali")

    return render(
        request,
        "logistica/proyectos/vista_global.html",
        {
            "todos_macroproyectos": todos_macroproyectos,
            "todos_proyectos": todos_proyectos_raw,
            "proyectos_js": json.dumps(proyectos_js),
            "macro_seleccionado": macro_seleccionado,
            "proyecto_seleccionado": proyecto_seleccionado,
            "proyectos_scope": proyectos_scope,
            "es_consolidado": es_consolidado,
            "proyectos_macro_list": proyectos_macro_list,
            "maniobra_emcali_display": maniobra_emcali_display,
            "maniobra_cointeca_display": maniobra_cointeca_display,
            "nota_tecnica_red": nota_tecnica_red,
            "apoyos": apoyos,
            "materiales_columnas": materiales_columnas,
            "filas_matriz": filas_matriz,
            "fila_totales": fila_totales,
            "tabla_resumen_retiros": tabla_resumen_retiros,
            "balance_materiales": balance_materiales,
            "materiales_devolucion": materiales_devolucion,
            "total_devolucion": total_devolucion,
            "entradas": entradas,
            "retiros_actas": retiros_actas,
            "total_items_requeridos": total_items_requeridos,
            "total_items_instalados": total_items_instalados,
            "total_items_entrados": total_items_entrados,
            "total_items_retirados": total_items_retirados,
            "total_material_sobrante": total_material_sobrante,
            "total_nodos": len(apoyos),
            "query": query,
            "tipo_filtro": tipo_filtro,
        }
    )


@login_required
def exportar_vista_global_excel(request):
    """
    Descarga el reporte completo en formato Excel (.xlsx) con 2 hojas:
    1. Matriz de Liquidación y Balance (Estilo Edson con Suministrado, Instalado, Retirado y Material que Sobra).
    2. Matriz de Nodos Poste a Poste (con columnas técnicas: Proyecto, Maniobras, Fecha, Dirección, Tipo Instalación,
       Tipo Estructura, Retenidas, Luminarias y Materiales instalados/retirados).
    """
    proyecto_id = request.GET.get("proyecto_id")
    macroproyecto_id = request.GET.get("macroproyecto_id")

    macroproyecto = None
    if macroproyecto_id and str(macroproyecto_id).isdigit():
        macroproyecto = Macroproyecto.objects.filter(id=int(macroproyecto_id)).first()

    proyecto = None
    es_consolidado = False
    if proyecto_id and str(proyecto_id).isdigit():
        proyecto = Proyecto.objects.filter(id=int(proyecto_id)).select_related("macroproyecto").first()
        proyectos_scope = Proyecto.objects.filter(id=proyecto.id) if proyecto else Proyecto.objects.none()
    elif proyecto_id == "todos" or (macroproyecto and not proyecto_id):
        es_consolidado = True
        if macroproyecto:
            proyectos_scope = Proyecto.objects.filter(macroproyecto=macroproyecto).select_related("macroproyecto")
        else:
            proyectos_scope = Proyecto.objects.all().select_related("macroproyecto")
    elif Proyecto.objects.exists():
        proyecto = Proyecto.objects.first()
        proyectos_scope = Proyecto.objects.filter(id=proyecto.id)
    else:
        return redirect("vista_global_logistica")

    # 1. Datos para Balance
    inst_qs = (
        ApoyoMaterial.objects.filter(apoyo__proyecto__in=proyectos_scope)
        .values("material_id")
        .annotate(total=Sum("cantidad_requerida"))
    )
    inst_map = {item["material_id"]: item["total"] for item in inst_qs}

    ent_qs = (
        DetalleEntradaMaterial.objects.filter(entrada__proyecto__in=proyectos_scope)
        .values("material_id")
        .annotate(total=Sum("cantidad"))
    )
    ent_map = {item["material_id"]: item["total"] for item in ent_qs}

    ret_qs = (
        ApoyoMaterial.objects.filter(apoyo__proyecto__in=proyectos_scope)
        .values("material_id")
        .annotate(total=Sum("cantidad_retirada"))
    )
    ret_map = {item["material_id"]: item["total"] for item in ret_qs if item["total"] > 0}

    all_mat_ids = set(inst_map.keys()) | set(ent_map.keys()) | set(ret_map.keys())
    materiales_db = Material.objects.filter(id__in=all_mat_ids).select_related("inventario").order_by("item", "descripcion")

    # 2. Datos para Nodos
    apoyos = (
        Apoyo.objects
        .filter(proyecto__in=proyectos_scope)
        .select_related("quien_ejecuta", "proyecto", "proyecto__macroproyecto")
        .prefetch_related("luminarias")
        .order_by("proyecto__numero_emcali", "numero_apoyo", "id")
    )
    apoyo_materiales = ApoyoMaterial.objects.filter(apoyo__proyecto__in=proyectos_scope).select_related("material")
    materiales_ids_nodos = apoyo_materiales.values_list('material_id', flat=True).distinct()
    materiales_columnas = list(Material.objects.filter(id__in=materiales_ids_nodos).order_by("item", "descripcion"))

    cantidades_inst_map = {}
    cantidades_ret_map = {}
    for am in apoyo_materiales:
        cantidades_inst_map[(am.apoyo_id, am.material_id)] = am.cantidad_requerida
        cantidades_ret_map[(am.apoyo_id, am.material_id)] = am.cantidad_retirada

    wb = openpyxl.Workbook()

    font_titulo = Font(name="Calibri", size=13, bold=True, color="1E3A8A")
    font_subtitulo = Font(name="Calibri", size=10, bold=True, color="4B5563")
    font_header = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    font_data = Font(name="Calibri", size=10, color="111827")
    font_total = Font(name="Calibri", size=10, bold=True, color="1E3A8A")

    fill_header = PatternFill(start_color="1E40AF", end_color="1E40AF", fill_type="solid")
    fill_total = PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid")
    fill_zebra = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

    thin_border_side = Side(border_style="thin", color="CBD5E1")
    border_cell = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
    border_total = Border(top=Side(border_style="medium", color="1E40AF"), bottom=Side(border_style="double", color="1E40AF"), left=thin_border_side, right=thin_border_side)

    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")

    # HOJA 1: MATRIZ DE BALANCE
    ws1 = wb.active
    ws1.title = "Matriz de Balance"

    nombre_scope = f"PROYECTO {proyecto.numero_emcali}" if proyecto else f"CONSOLIDADO ({macroproyecto.nombre if macroproyecto else 'GLOBAL'})"
    ws1.merge_cells("A1:H1")
    ws1["A1"] = f"COINTECA S.A.S. — LIQUIDACIÓN Y BALANCE DE MATERIALES ({nombre_scope})"
    ws1["A1"].font = font_titulo
    ws1["A1"].alignment = align_left

    macro_nom = macroproyecto.nombre if macroproyecto else (proyecto.macroproyecto.nombre if proyecto and proyecto.macroproyecto else "Sin Macroproyecto")
    maniobras_txt = ""
    if macroproyecto:
        maniobras_txt = f" | MANIOBRA EMCALI: {macroproyecto.numero_maniobra_emcali or 'N/A'} | MANIOBRA COINTECA: {macroproyecto.numero_maniobra_cointeca or 'N/A'}"
    elif proyecto and proyecto.macroproyecto:
        maniobras_txt = f" | MANIOBRA EMCALI: {proyecto.macroproyecto.numero_maniobra_emcali or 'N/A'} | MANIOBRA COINTECA: {proyecto.macroproyecto.numero_maniobra_cointeca or 'N/A'}"

    ws1.merge_cells("A2:H2")
    ws1["A2"] = f"MACROPROYECTO: {macro_nom}{maniobras_txt} | NODOS: {apoyos.count()} | FECHA: {timezone.now().strftime('%d/%m/%Y')}"
    ws1["A2"].font = font_subtitulo
    ws1["A2"].alignment = align_left

    ws1.append([])
    headers1 = [
        "ÍTEM",
        "DESCRIPCIÓN DEL MATERIAL",
        "UNIDAD",
        "SUMINISTRADO (ENTRADAS)",
        "INSTALADO EN POSTES",
        "RETIRADO / DESMONTE",
        "MATERIAL QUE SOBRA",
        "STOCK EN BODEGA"
    ]
    ws1.append(headers1)

    for col in range(1, 9):
        c = ws1.cell(row=4, column=col)
        c.font = font_header
        c.fill = fill_header
        c.alignment = align_center if col != 2 else align_left
        c.border = border_cell

    row_idx = 5
    tot_ent = Decimal("0")
    tot_inst = Decimal("0")
    tot_ret = Decimal("0")
    tot_sob = Decimal("0")
    materiales_devolucion = []

    def fmt_v(v):
        if v is None:
            return 0
        return int(v) if v % 1 == 0 else float(v)

    for idx, mat in enumerate(materiales_db, start=1):
        c_ent = ent_map.get(mat.id, Decimal("0"))
        c_inst = inst_map.get(mat.id, Decimal("0"))
        c_ret = ret_map.get(mat.id, Decimal("0"))
        c_sob = c_ent - c_inst
        c_dev = max(Decimal("0"), c_sob)
        stock_obj = getattr(mat, "inventario", None)
        c_stock = stock_obj.cantidad if stock_obj else Decimal("0")

        tot_ent += c_ent
        tot_inst += c_inst
        tot_ret += c_ret
        tot_sob += c_sob

        if c_dev > 0:
            materiales_devolucion.append({
                "mat": mat,
                "ent": c_ent,
                "inst": c_inst,
                "dev": c_dev,
                "stock": c_stock
            })

        ws1.append([
            mat.item or "",
            mat.descripcion,
            mat.unidad or "UN",
            fmt_v(c_ent),
            fmt_v(c_inst),
            fmt_v(c_ret),
            fmt_v(c_sob),
            fmt_v(c_stock)
        ])
        for col in range(1, 9):
            c = ws1.cell(row=row_idx, column=col)
            c.font = font_data
            c.border = border_cell
            if idx % 2 == 0:
                c.fill = fill_zebra
            if col in [1, 3]:
                c.alignment = align_center
            elif col == 2:
                c.alignment = align_left
            else:
                c.alignment = align_right
                c.number_format = "#,##0" if isinstance(c.value, int) else "0.##"
        row_idx += 1

    ws1.append([
        "",
        "TOTALES CONSOLIDADOS",
        f"{len(materiales_db)} ÍTEMS",
        fmt_v(tot_ent),
        fmt_v(tot_inst),
        fmt_v(tot_ret),
        fmt_v(tot_sob),
        "—"
    ])
    for col in range(1, 9):
        c = ws1.cell(row=row_idx, column=col)
        c.font = font_total
        c.fill = fill_total
        c.border = border_total
        if col in [1, 3, 8]:
            c.alignment = align_center
        elif col == 2:
            c.alignment = align_left
        else:
            c.alignment = align_right
            c.number_format = "#,##0" if isinstance(c.value, int) else "0.##"

    ws1.column_dimensions["A"].width = 12
    ws1.column_dimensions["B"].width = 46
    ws1.column_dimensions["C"].width = 12
    ws1.column_dimensions["D"].width = 24
    ws1.column_dimensions["E"].width = 22
    ws1.column_dimensions["F"].width = 22
    ws1.column_dimensions["G"].width = 22
    ws1.column_dimensions["H"].width = 18

    # HOJA 2: MATRIZ DE NODOS POSTE A POSTE
    ws2 = wb.create_sheet(title="Nodos Poste a Poste")
    ws2.merge_cells("A1:K1")
    ws2["A1"] = f"COINTECA S.A.S. — MATRIZ POSTE A POSTE ({nombre_scope})"
    ws2["A1"].font = font_titulo
    ws2["A1"].alignment = align_left

    ws2.append([])
    fixed_headers = [
        "PROYECTO",
        "QUIÉN EJECUTA",
        "NODO / POSTE",
        "N° APOYO",
        "FECHA",
        "DIRECCIÓN / BARRIO",
        "TIPO INSTALACIÓN",
        "TIPO ESTRUCTURA",
        "CANT. RETENIDA",
        "METROS RETENIDO",
        "ESTADO",
        "POTENCIA",
        "CÓDIGO LUM."
    ]
    mat_headers = [f"{m.descripcion} ({m.unidad or 'UN'})" for m in materiales_columnas]
    ws2.append(fixed_headers + mat_headers)
    total_cols = len(fixed_headers) + len(mat_headers)

    for col in range(1, total_cols + 1):
        c = ws2.cell(row=3, column=col)
        c.font = font_header
        c.fill = fill_header
        c.alignment = align_center if col not in [2, 6] else align_left
        c.border = border_cell

    row_nodos = 4
    totales_mat_nodos = {m.id: Decimal("0") for m in materiales_columnas}

    for idx, ap in enumerate(apoyos, start=1):
        proy_txt = ap.proyecto.numero_emcali if ap.proyecto else "—"
        quien = ap.quien_ejecuta.nombre_completo if ap.quien_ejecuta else "Sin asignar"
        nodo_str = ap.nodo or "Sin Nodo"
        num_ap = ap.numero_apoyo or "—"
        fecha_str = ap.fecha.strftime("%d/%m/%Y") if ap.fecha else "—"
        dir_str = ap.direccion or "—"
        tipo_inst = ap.tipo_instalacion or "—"
        tipo_est = ap.tipo_estructura or "—"
        cant_ret = fmt_v(ap.cantidad_retenida) if ap.cantidad_retenida is not None else "—"
        met_ret = fmt_v(ap.metros_retenido) if ap.metros_retenido is not None else "—"
        est = ap.estado
        lums = ap.luminarias.all()
        potencias_str = ", ".join(l.potencia for l in lums if l.potencia) or "—"
        codigos_str = ", ".join(l.codigo for l in lums if l.codigo) or "—"

        row_data = [
            proy_txt,
            quien,
            nodo_str,
            num_ap,
            fecha_str,
            dir_str,
            tipo_inst,
            tipo_est,
            cant_ret,
            met_ret,
            est,
            potencias_str,
            codigos_str
        ]

        for m in materiales_columnas:
            c_inst = cantidades_inst_map.get((ap.id, m.id), Decimal("0"))
            c_ret = cantidades_ret_map.get((ap.id, m.id), Decimal("0"))
            totales_mat_nodos[m.id] += c_inst
            if c_ret > 0 and c_inst > 0:
                celda_txt = f"{fmt_v(c_inst)} (Ret:{fmt_v(c_ret)})"
            elif c_ret > 0:
                celda_txt = f"Ret:{fmt_v(c_ret)}"
            elif c_inst > 0:
                celda_txt = str(fmt_v(c_inst))
            else:
                celda_txt = "—"
            row_data.append(celda_txt)

        ws2.append(row_data)
        for col in range(1, total_cols + 1):
            c = ws2.cell(row=row_nodos, column=col)
            c.font = font_data
            c.border = border_cell
            if idx % 2 == 0:
                c.fill = fill_zebra
            if col in [1, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13] or col > 13:
                c.alignment = align_center
            else:
                c.alignment = align_left
        row_nodos += 1

    # Totales hoja 2
    row_tot_nodos = ["TOTALES", f"{len(apoyos)} NODOS", "", "", "", "", "", "", "", "", "", "", ""]
    for m in materiales_columnas:
        row_tot_nodos.append(fmt_v(totales_mat_nodos[m.id]))
    ws2.append(row_tot_nodos)

    for col in range(1, total_cols + 1):
        c = ws2.cell(row=row_nodos, column=col)
        c.font = font_total
        c.fill = fill_total
        c.border = border_total
        c.alignment = align_center if col > 1 else align_left

    ws2.column_dimensions["A"].width = 16
    ws2.column_dimensions["B"].width = 24
    ws2.column_dimensions["C"].width = 16
    ws2.column_dimensions["D"].width = 12
    ws2.column_dimensions["E"].width = 14
    ws2.column_dimensions["F"].width = 28
    ws2.column_dimensions["G"].width = 18
    ws2.column_dimensions["H"].width = 18
    ws2.column_dimensions["I"].width = 14
    ws2.column_dimensions["J"].width = 14
    ws2.column_dimensions["K"].width = 14
    ws2.column_dimensions["L"].width = 16
    ws2.column_dimensions["M"].width = 18
    for c_idx in range(14, total_cols + 1):
        col_letter = get_column_letter(c_idx)
        ws2.column_dimensions[col_letter].width = 20

    # HOJA 3: DEVOLUCIÓN A BODEGA (REINTEGROS)
    if materiales_devolucion:
        ws3 = wb.create_sheet(title="Devolución a Bodega")
        ws3.merge_cells("A1:G1")
        ws3["A1"] = f"COINTECA S.A.S. — MATERIALES DE DEVOLUCIÓN A BODEGA ({nombre_scope})"
        ws3["A1"].font = font_titulo
        ws3["A1"].alignment = align_left

        ws3.merge_cells("A2:G2")
        ws3["A2"] = f"MATERIALES SOBRANTES CONSOLIDADOS TRAS INSTALACIÓN  |  FECHA: {timezone.now().strftime('%d/%m/%Y')}"
        ws3.append([])
        ws3_headers = [
            "ÍTEM",
            "DESCRIPCIÓN DEL MATERIAL",
            "UNIDAD",
            "SUMINISTRADO (ENTRADAS)",
            "INSTALADO EN POSTES",
            "CANTIDAD A DEVOLVER / REINTEGRAR",
            "STOCK ACTUAL EN BODEGA"
        ]
        ws3.append(ws3_headers)

        for col in range(1, 8):
            c = ws3.cell(row=4, column=col)
            c.font = font_header
            c.fill = fill_header
            c.alignment = align_center if col != 2 else align_left
            c.border = border_cell

        row3_idx = 5
        tot_d_ent = Decimal("0")
        tot_d_inst = Decimal("0")
        tot_d_dev = Decimal("0")

        for idx, d in enumerate(materiales_devolucion, start=1):
            tot_d_ent += d["ent"]
            tot_d_inst += d["inst"]
            tot_d_dev += d["dev"]

            ws3.append([
                d["mat"].item or "",
                d["mat"].descripcion,
                d["mat"].unidad or "UN",
                fmt_v(d["ent"]),
                fmt_v(d["inst"]),
                fmt_v(d["dev"]),
                fmt_v(d["stock"])
            ])

            for col in range(1, 8):
                c = ws3.cell(row=row3_idx, column=col)
                c.font = font_data
                c.border = border_cell
                if idx % 2 == 0:
                    c.fill = fill_zebra
                if col in [1, 3]:
                    c.alignment = align_center
                elif col == 2:
                    c.alignment = align_left
                else:
                    c.alignment = align_right
                    c.number_format = "#,##0" if isinstance(c.value, int) else "0.##"
            row3_idx += 1

        ws3.append([
            "",
            "TOTAL A DEVOLVER A BODEGA",
            f"{len(materiales_devolucion)} ÍTEMS",
            fmt_v(tot_d_ent),
            fmt_v(tot_d_inst),
            fmt_v(tot_d_dev),
            "—"
        ])
        for col in range(1, 8):
            c = ws3.cell(row=row3_idx, column=col)
            c.font = font_total
            c.fill = fill_total
            c.border = border_total
            if col in [1, 3, 7]:
                c.alignment = align_center
            elif col == 2:
                c.alignment = align_left
            else:
                c.alignment = align_right
                c.number_format = "#,##0" if isinstance(c.value, int) else "0.##"

        ws3.column_dimensions["A"].width = 12
        ws3.column_dimensions["B"].width = 48
        ws3.column_dimensions["C"].width = 12
        ws3.column_dimensions["D"].width = 24
        ws3.column_dimensions["E"].width = 22
        ws3.column_dimensions["F"].width = 28
        ws3.column_dimensions["G"].width = 20

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    nombre_slug = proyecto.numero_emcali if proyecto else (macroproyecto.nombre.replace(" ", "_") if macroproyecto else "Consolidado_Global")
    filename = f"Vista_Global_{nombre_slug}_{timezone.now().strftime('%Y%m%d_%H%M')}.xlsx"
    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response