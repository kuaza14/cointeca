from collections import defaultdict
from core.helpers.ingenieria_calculo import calcular_mano_obra_proyecto_completo, calcular_mano_obra_para_apoyo, actualizar_presupuesto_proyecto
from core.helpers.inventario_historial import registrar_movimiento_inventario
import io
import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from decimal import Decimal
from django.db.models import Sum, Q
from django.utils import timezone
from core.models import (
    Macroproyecto,
    Proyecto,
    Apoyo,
    Material,
    ApoyoMaterial,
    ApoyoLuminaria,
    Empleado,
    Inventario,
    EntradaMaterialProyecto,
    DetalleEntradaMaterial,
    DetalleDevolucionMaterial,
    ItemManoObra,
    ApoyoManoObra,
    Presupuesto,
    MovimientoInventario,
)
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def ingenieria_inicio(request):
    return render(
        request,
        "ingenieria/ingenieria_inicio.html"
    )

# ==============================================================================
# 🏢 GESTIÓN DE MACROPROYECTOS (INGENIERÍA)
# ==============================================================================

@login_required
def lista_macroproyectos(request):
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
        num_proyectos = macro.proyectos.count()
        num_apoyos = Apoyo.objects.filter(proyecto__macroproyecto=macro).count()
        resumen_macros.append({
            "macro": macro,
            "num_proyectos": num_proyectos,
            "num_apoyos": num_apoyos,
        })

    proyectos_imprimir = Proyecto.objects.all().select_related("macroproyecto").prefetch_related("apoyos").order_by("numero_emcali")

    return render(
        request,
        "ingenieria/macroproyectos/lista.html",
        {
            "macroproyectos": resumen_macros,
            "proyectos_imprimir": proyectos_imprimir,
            "query": query,
            "total_macros": Macroproyecto.objects.count(),
            "total_filtrados": len(resumen_macros),
        }
    )

@login_required
def crear_macroproyecto(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        numero_maniobra_emcali = request.POST.get("numero_maniobra_emcali", "").strip()
        numero_maniobra_cointeca = request.POST.get("numero_maniobra_cointeca", "").strip()
        descripcion = request.POST.get("descripcion", "").strip()
        estado = request.POST.get("estado", Macroproyecto.Estados.PLANEACION).strip()

        if not nombre:
            messages.error(request, "El nombre del macroproyecto es obligatorio.")
            return redirect("lista_macroproyectos")

        if Macroproyecto.objects.filter(nombre__iexact=nombre).exists():
            messages.error(request, f"Ya existe un macroproyecto registrado con el nombre '{nombre}'.")
            return redirect("lista_macroproyectos")

        tipo = request.POST.get("tipo", Macroproyecto.Tipos.AP).strip()
        if tipo not in Macroproyecto.Tipos.values:
            tipo = Macroproyecto.Tipos.AP

        macro = Macroproyecto.objects.create(
            nombre=nombre,
            tipo=tipo,
            numero_maniobra_emcali=numero_maniobra_emcali,
            numero_maniobra_cointeca=numero_maniobra_cointeca,
            descripcion=descripcion,
            estado=estado if estado in Macroproyecto.Estados.values else Macroproyecto.Estados.PLANEACION
        )
        messages.success(request, f"{macro.etiqueta} '{macro.nombre}' creado exitosamente.")
        return redirect("lista_macroproyectos")
    return redirect("lista_macroproyectos")

@login_required
def editar_macroproyecto(request, id):
    macro = get_object_or_404(Macroproyecto, id=id)

    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        tipo_actual = getattr(macro, "tipo", Macroproyecto.Tipos.AP)
        tipo = request.POST.get("tipo", tipo_actual).strip()
        numero_maniobra_emcali = request.POST.get("numero_maniobra_emcali", "").strip()
        numero_maniobra_cointeca = request.POST.get("numero_maniobra_cointeca", "").strip()
        descripcion = request.POST.get("descripcion", "").strip()
        estado = request.POST.get("estado", macro.estado).strip()

        if not nombre:
            messages.error(request, f"El nombre del {macro.etiqueta.lower()} es obligatorio.")
            return redirect("lista_macroproyectos")

        if Macroproyecto.objects.filter(nombre__iexact=nombre).exclude(id=macro.id).exists():
            messages.error(request, f"Ya existe otro {macro.etiqueta.lower()} con el nombre '{nombre}'.")
            return redirect("lista_macroproyectos")

        macro.nombre = nombre
        if tipo in Macroproyecto.Tipos.values:
            if tipo != tipo_actual:
                if tipo == Macroproyecto.Tipos.MT and macro.proyectos.exclude(tipo=Proyecto.Tipos.MT).exists():
                    messages.error(request, f"No se puede cambiar a Circuito (MT) porque ya contiene proyectos de Alumbrado Público (AP).")
                    return redirect("lista_macroproyectos")
                elif tipo == Macroproyecto.Tipos.AP and macro.proyectos.filter(tipo=Proyecto.Tipos.MT).exists():
                    messages.error(request, f"No se puede cambiar a Macroproyecto (AP) porque ya contiene maniobras de Media Tensión (MT).")
                    return redirect("lista_macroproyectos")
            macro.tipo = tipo
        if "numero_maniobra_emcali" in request.POST:
            macro.numero_maniobra_emcali = request.POST.get("numero_maniobra_emcali", "").strip()
        if "numero_maniobra_cointeca" in request.POST:
            macro.numero_maniobra_cointeca = request.POST.get("numero_maniobra_cointeca", "").strip()
        macro.descripcion = descripcion
        if estado in Macroproyecto.Estados.values:
            macro.estado = estado
        macro.save()

        messages.success(request, f"{macro.etiqueta} '{macro.nombre}' actualizado correctamente.")
        return redirect("lista_macroproyectos")
    return redirect("lista_macroproyectos")

@login_required
@transaction.atomic
def eliminar_macroproyecto(request, id):
    macro = Macroproyecto.objects.filter(id=id).first()
    if not macro:
        messages.warning(request, "El registro que intentas eliminar ya no existe.")
        return redirect("lista_macroproyectos")

    if request.method == "POST":
        nombre = macro.nombre
        etiqueta = getattr(macro, "etiqueta", "Macroproyecto")
        etiqueta_hijo_pl = getattr(macro, "etiqueta_hijo_plural", "Proyectos").lower()
        macro.delete()
        messages.success(request, f"{etiqueta} '{nombre}' y todos sus {etiqueta_hijo_pl} asociados han sido eliminados.")
    return redirect("lista_macroproyectos")

# ==============================================================================
# 📑 GESTIÓN DE PROYECTOS / MICROPROYECTOS
# ==============================================================================

@login_required
def lista_proyectos(request, macroproyecto_id=None):
    query = request.GET.get("q", "").strip()
    macroproyecto = None

    if macroproyecto_id:
        macroproyecto = get_object_or_404(Macroproyecto, id=macroproyecto_id)
        proyectos = Proyecto.objects.filter(macroproyecto=macroproyecto)
    else:
        macro_param = request.GET.get("macroproyecto_id")
        if macro_param and str(macro_param).isdigit():
            macroproyecto = Macroproyecto.objects.filter(id=int(macro_param)).first()
            proyectos = Proyecto.objects.filter(macroproyecto=macroproyecto) if macroproyecto else Proyecto.objects.all()
        else:
            proyectos = Proyecto.objects.all()

    if macroproyecto:
        proyectos_imprimir = Proyecto.objects.filter(macroproyecto=macroproyecto).select_related("macroproyecto").prefetch_related("apoyos").order_by("numero_emcali")
    else:
        proyectos_imprimir = Proyecto.objects.all().select_related("macroproyecto").prefetch_related("apoyos").order_by("numero_emcali")

    if query:
        proyectos = proyectos.filter(
            Q(numero_emcali__icontains=query) |
            Q(numero_cointeca__icontains=query) |
            Q(tipo__icontains=query) |
            Q(estado__icontains=query)
        )

    proyectos = proyectos.select_related("macroproyecto").order_by("-id")
    todos_macroproyectos = Macroproyecto.objects.all().order_by("nombre")

    total_proy = Proyecto.objects.filter(macroproyecto=macroproyecto).count() if macroproyecto else Proyecto.objects.count()

    return render(
        request,
        "ingenieria/proyecto/lista.html",
        {
            "macroproyecto": macroproyecto,
            "proyectos": proyectos,
            "proyectos_imprimir": proyectos_imprimir,
            "macroproyectos": todos_macroproyectos,
            "query": query,
            "total_proyectos": total_proy,
            "total_filtrados": proyectos.count(),
        }
    )

@login_required
def crear_proyecto(request, macroproyecto_id=None):
    if request.method == "POST":
        numero_emcali = request.POST.get("numero_emcali", "").strip()
        numero_cointeca = request.POST.get("numero_cointeca", "").strip()
        tipo = request.POST.get("tipo", "").strip()
        estado = request.POST.get("estado", Proyecto.Estados.PLANEACION).strip()
        m_id = request.POST.get("macroproyecto_id") or macroproyecto_id

        macroproyecto = None
        if m_id and str(m_id).isdigit():
            macroproyecto = Macroproyecto.objects.filter(id=int(m_id)).first()

        def _volver():
            origen = request.POST.get("origen", "").strip()
            if origen == "logistica":
                if macroproyecto:
                    return redirect("proyectos_logistica_por_macroproyecto", macroproyecto_id=macroproyecto.id)
                return redirect("proyectos_logistica")
            if macroproyecto:
                return redirect("proyectos_por_macroproyecto", macroproyecto_id=macroproyecto.id)
            return redirect("lista_proyectos")

        if not numero_emcali or not tipo:
            messages.error(request, "El número y el tipo de red son obligatorios.")
            return _volver()

        # Validar coherencia entre Macroproyecto (AP) y Circuito (MT)
        if macroproyecto:
            if macroproyecto.es_mt and tipo != Proyecto.Tipos.MT:
                messages.error(
                    request,
                    f"El contenedor '{macroproyecto.nombre}' es un Circuito de Media Tensión. Solo se pueden crear maniobras de tipo Media Tensión (MT)."
                )
                return _volver()
            elif macroproyecto.es_ap and tipo == Proyecto.Tipos.MT:
                messages.error(
                    request,
                    f"El contenedor '{macroproyecto.nombre}' es un Macroproyecto de Alumbrado Público. Solo se pueden crear proyectos de Alumbrado Público (AP), no maniobras de Media Tensión."
                )
                return _volver()

        # Validar si ya existe en el MISMO Macroproyecto o Circuito
        filtro_existente = Proyecto.objects.filter(
            numero_emcali__iexact=numero_emcali,
            macroproyecto=macroproyecto
        )
        if filtro_existente.exists():
            etiqueta_padre = macroproyecto.etiqueta if macroproyecto else "Macroproyecto"
            etiqueta_hijo = macroproyecto.etiqueta_hijo if macroproyecto else "Proyecto"
            if macroproyecto:
                messages.error(request, f"Ya existe una {etiqueta_hijo.lower()} con el número '{numero_emcali}' en el {etiqueta_padre.lower()} '{macroproyecto.nombre}'.")
            else:
                messages.error(request, f"Ya existe un proyecto sin macroproyecto con el número '{numero_emcali}'.")
            return _volver()

        proyecto = Proyecto.objects.create(
            macroproyecto=macroproyecto,
            numero_emcali=numero_emcali,
            numero_cointeca=numero_cointeca if tipo == Proyecto.Tipos.MT else "",
            tipo=tipo,
            estado=estado if estado in Proyecto.Estados.values else Proyecto.Estados.PLANEACION
        )
        messages.success(request, f"{proyecto.etiqueta} '{proyecto.numero_emcali}' creado exitosamente.")
        return _volver()

    if macroproyecto_id:
        return redirect("proyectos_por_macroproyecto", macroproyecto_id=macroproyecto_id)
    return redirect("lista_proyectos")

@login_required
def editar_proyecto(request, id):
    proyecto = get_object_or_404(Proyecto, id=id)

    if request.method == "POST":
        numero_emcali = request.POST.get("numero_emcali", "").strip()
        numero_cointeca = request.POST.get("numero_cointeca", "").strip()
        tipo = request.POST.get("tipo", "").strip()
        estado = request.POST.get("estado", proyecto.estado).strip()
        m_id = request.POST.get("macroproyecto_id")

        if m_id and str(m_id).isdigit():
            proyecto.macroproyecto = Macroproyecto.objects.filter(id=int(m_id)).first()
        elif m_id == "":
            proyecto.macroproyecto = None

        def _volver():
            if proyecto.macroproyecto:
                return redirect("proyectos_por_macroproyecto", macroproyecto_id=proyecto.macroproyecto.id)
            return redirect("lista_proyectos")

        if not numero_emcali or not tipo:
            messages.error(request, f"El número de {proyecto.etiqueta.lower()} y el tipo de red son obligatorios.")
            return _volver()

        # Validar coherencia entre Macroproyecto (AP) y Circuito (MT)
        if proyecto.macroproyecto:
            if proyecto.macroproyecto.es_mt and tipo != Proyecto.Tipos.MT:
                messages.error(
                    request,
                    f"El contenedor '{proyecto.macroproyecto.nombre}' es un Circuito de Media Tensión. Solo se permiten maniobras de tipo Media Tensión (MT)."
                )
                return _volver()
            elif proyecto.macroproyecto.es_ap and tipo == Proyecto.Tipos.MT:
                messages.error(
                    request,
                    f"El contenedor '{proyecto.macroproyecto.nombre}' es un Macroproyecto de Alumbrado Público. Solo se permiten proyectos de Alumbrado Público (AP), no maniobras de Media Tensión."
                )
                return _volver()

        # Validar si ya existe en el MISMO Macroproyecto o Circuito
        filtro_existente = Proyecto.objects.filter(
            numero_emcali__iexact=numero_emcali,
            macroproyecto=proyecto.macroproyecto
        ).exclude(id=proyecto.id)
        if filtro_existente.exists():
            etiqueta_padre = proyecto.macroproyecto.etiqueta if proyecto.macroproyecto else "Macroproyecto"
            etiqueta_hijo = proyecto.macroproyecto.etiqueta_hijo if proyecto.macroproyecto else "Proyecto"
            if proyecto.macroproyecto:
                messages.error(request, f"Ya existe una {etiqueta_hijo.lower()} con el número '{numero_emcali}' en el {etiqueta_padre.lower()} '{proyecto.macroproyecto.nombre}'.")
            else:
                messages.error(request, f"Ya existe otro proyecto registrado con el número '{numero_emcali}'.")
            return _volver()

        proyecto.numero_emcali = numero_emcali
        proyecto.tipo = tipo
        if tipo == Proyecto.Tipos.MT:
            proyecto.numero_cointeca = numero_cointeca
        else:
            proyecto.numero_cointeca = ""
        if estado in Proyecto.Estados.values:
            proyecto.estado = estado
        proyecto.save()

        messages.success(request, f"{proyecto.etiqueta} '{proyecto.numero_emcali}' actualizado correctamente.")
        return _volver()

    if proyecto.macroproyecto:
        return redirect("proyectos_por_macroproyecto", macroproyecto_id=proyecto.macroproyecto.id)
    return redirect("lista_proyectos")

@login_required
@transaction.atomic
def eliminar_proyecto(request, id):
    proyecto = Proyecto.objects.filter(id=id).first()
    if not proyecto:
        messages.warning(request, "El registro que intentas eliminar ya no existe.")
        return redirect("lista_proyectos")

    macro_id = proyecto.macroproyecto_id
    etiqueta = getattr(proyecto, "etiqueta", "Proyecto")
    if request.method == "POST":
        nombre = proyecto.numero_emcali
        proyecto.delete()
        messages.success(request, f"{etiqueta} '{nombre}' y todos sus apoyos/materiales han sido eliminados correctamente.")
    
    if macro_id:
        return redirect("proyectos_por_macroproyecto", macroproyecto_id=macro_id)
    return redirect("lista_proyectos")

@login_required
def detalle_proyecto(request, id):
    proyecto = get_object_or_404(Proyecto, id=id)

    # 1. Cargar apoyos con sus relaciones principales en 1 sola consulta
    apoyos = list(
        Apoyo.objects
        .filter(proyecto=proyecto)
        .select_related("quien_ejecuta")
        .prefetch_related("luminarias")
        .order_by("numero_apoyo", "id")
    )

    tab_activa = request.GET.get("tab", "materiales").strip().lower()

    # 2. Cargar TODOS los materiales de los apoyos del proyecto en 1 sola consulta (sin N+1)
    apoyo_materiales = list(
        ApoyoMaterial.objects.filter(
            apoyo__proyecto=proyecto
        ).select_related("material", "material__inventario").order_by("material__descripcion")
    )

    materiales_dict = {}
    cantidades_inst_map = {}
    cantidades_ret_map = {}
    apoyo_materiales_map = defaultdict(list)

    for am in apoyo_materiales:
        cantidades_inst_map[(am.apoyo_id, am.material_id)] = am.cantidad_requerida
        cantidades_ret_map[(am.apoyo_id, am.material_id)] = am.cantidad_retirada
        apoyo_materiales_map[am.apoyo_id].append(am)
        if am.material_id not in materiales_dict:
            materiales_dict[am.material_id] = am.material

    materiales_columnas = sorted(materiales_dict.values(), key=lambda m: (m.item or "", m.descripcion or ""))

    filas_matriz = []
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
            "materiales_asociados": apoyo_materiales_map.get(ap.id, []),
        })

    fila_totales = []
    for mat in materiales_columnas:
        fila_totales.append({
            "material": mat,
            "total": totales_inst_columna.get(mat.id, Decimal("0")),
            "total_retirado": totales_ret_columna.get(mat.id, Decimal("0")),
        })

    tabla_resumen_retiros = []
    for mat in materiales_columnas:
        tot_ret = totales_ret_columna.get(mat.id, Decimal("0"))
        if tot_ret > 0:
            tabla_resumen_retiros.append({
                "material": mat,
                "cantidad_retirada": tot_ret,
            })

    # Entradas suministradas a este proyecto y devoluciones
    ent_qs = (
        DetalleEntradaMaterial.objects.filter(entrada__proyecto=proyecto)
        .values("material_id")
        .annotate(total=Sum("cantidad"))
    )
    ent_map = {item["material_id"]: item["total"] for item in ent_qs}

    dev_qs = (
        DetalleDevolucionMaterial.objects.filter(devolucion__proyecto=proyecto)
        .values("material_id")
        .annotate(total=Sum("cantidad"))
    )
    dev_map = {item["material_id"]: item["total"] for item in dev_qs}

    todos_mat_ids_dev = set(totales_ret_columna.keys()) | set(ent_map.keys())
    mats_dev_db = Material.objects.filter(id__in=todos_mat_ids_dev).select_related("inventario")
    mats_dev_map = {m.id: m for m in mats_dev_db}

    tabla_resumen_devolucion = []
    for m_id in sorted(
        todos_mat_ids_dev,
        key=lambda mid: (mats_dev_map.get(mid).item or "", mats_dev_map.get(mid).descripcion or "")
        if mid in mats_dev_map else ("", "")
    ):
        mat = mats_dev_map.get(m_id)
        if not mat:
            continue
        c_ent = ent_map.get(m_id, Decimal("0"))
        c_inst = totales_inst_columna.get(m_id, Decimal("0"))
        c_ret = totales_ret_columna.get(m_id, Decimal("0"))
        c_dev_hecha = dev_map.get(m_id, Decimal("0"))
        c_sob = max(Decimal("0"), c_ent - c_inst)
        c_total_dev = max(Decimal("0"), (c_sob + c_ret) - c_dev_hecha)
        stock_obj = getattr(mat, "inventario", None)
        c_stock = stock_obj.cantidad if stock_obj else Decimal("0")

        if c_ret > 0 or c_sob > 0 or c_total_dev > 0:
            tabla_resumen_devolucion.append({
                "material": mat,
                "entrada": c_ent,
                "instalado": c_inst,
                "sobrante": c_sob,
                "retirado": c_ret,
                "devolucion": c_total_dev,
                "devolucion_realizada": c_dev_hecha,
                "stock_bodega": c_stock,
            })

    # 3. Cargar TODA la Mano de Obra del proyecto en 1 sola consulta (sin N+1)
    apoyos_mo = list(
        ApoyoManoObra.objects.filter(
            apoyo__proyecto=proyecto
        ).select_related("item_mano_obra")
    )

    mo_dict = {}
    mo_cant_map = {}
    mo_origen_map = {}
    mo_obs_map = {}
    mo_id_map = {}
    apoyo_mo_map = defaultdict(list)

    for amo in apoyos_mo:
        mo_cant_map[(amo.apoyo_id, amo.item_mano_obra_id)] = amo.cantidad
        mo_origen_map[(amo.apoyo_id, amo.item_mano_obra_id)] = amo.origen
        mo_obs_map[(amo.apoyo_id, amo.item_mano_obra_id)] = amo.observacion or ""
        mo_id_map[(amo.apoyo_id, amo.item_mano_obra_id)] = amo.id
        apoyo_mo_map[amo.apoyo_id].append(amo)
        if amo.item_mano_obra_id not in mo_dict:
            mo_dict[amo.item_mano_obra_id] = amo.item_mano_obra

    mo_columnas = sorted(mo_dict.values(), key=lambda item: item.codigo or "")

    mo_filas_matriz = []
    mo_totales_columna = {item.id: Decimal("0") for item in mo_columnas}

    for ap in apoyos:
        celdas_mo = []
        for item in mo_columnas:
            cant_mo = mo_cant_map.get((ap.id, item.id), Decimal("0"))
            orig = mo_origen_map.get((ap.id, item.id), "CALCULADO")
            obs = mo_obs_map.get((ap.id, item.id), "")
            amo_id = mo_id_map.get((ap.id, item.id))
            celdas_mo.append({
                "item": item,
                "cantidad": cant_mo,
                "origen": orig,
                "observacion": obs,
                "amo_id": amo_id,
            })
            mo_totales_columna[item.id] += cant_mo

        # Obtener observaciones de mano de obra manual para este apoyo
        obs_manuales = [
            f"[{amo.item_mano_obra.codigo}] {amo.observacion}"
            for amo in apoyo_mo_map.get(ap.id, [])
            if amo.origen == ApoyoManoObra.Origen.MANUAL and amo.observacion
        ]

        mo_filas_matriz.append({
            "apoyo": ap,
            "celdas": celdas_mo,
            "manos_obra_list": apoyo_mo_map.get(ap.id, []),
            "materiales_asociados": apoyo_materiales_map.get(ap.id, []),
            "observaciones_mo_manuales": obs_manuales,
        })

    mo_fila_totales = []
    gran_total_mo_pesos = Decimal("0")
    resumen_economico_items = []

    for item in mo_columnas:
        tot_c = mo_totales_columna.get(item.id, Decimal("0"))
        sub_pesos = tot_c * item.valor_unitario
        gran_total_mo_pesos += sub_pesos
        mo_fila_totales.append({
            "item": item,
            "total": tot_c,
            "total_pesos": sub_pesos,
        })
        if tot_c > 0:
            resumen_economico_items.append({
                "item": item,
                "cantidad": tot_c,
                "subtotal": sub_pesos,
            })

    presupuesto, _ = Presupuesto.objects.get_or_create(proyecto=proyecto)
    if presupuesto.valor_mano_obra != gran_total_mo_pesos:
        presupuesto.valor_mano_obra = gran_total_mo_pesos
        presupuesto.valor_total = presupuesto.valor_materiales + presupuesto.valor_mano_obra + presupuesto.otros_costos
        presupuesto.save(update_fields=['valor_mano_obra', 'valor_total'])

    materiales_catalogo = list(Material.objects.select_related('inventario').all().order_by("descripcion"))
    catalogo_mo_todos = list(ItemManoObra.objects.all().order_by("codigo"))
    empleados = list(Empleado.objects.filter(estado="activo").order_by("nombre_completo"))

    mat_cable_obj = (
        Material.objects.filter(item="43").first()
        or Material.objects.filter(descripcion__icontains="Cable para retenida EAR 3/8").first()
    )
    mat_cable_id = mat_cable_obj.id if mat_cable_obj else None

    return render(
        request,
        "ingenieria/proyecto/detalle_proyecto.html",
        {
            "proyecto": proyecto,
            "apoyos": apoyos,
            "tab_activa": tab_activa,
            "materiales_columnas": materiales_columnas,
            "filas_matriz": filas_matriz,
            "fila_totales": fila_totales,
            "tabla_resumen_retiros": tabla_resumen_retiros,
            "tabla_resumen_devolucion": tabla_resumen_devolucion,
            "materiales_catalogo": materiales_catalogo,
            "empleados": empleados,
            "mat_cable_id": mat_cable_id,
            # Mano de Obra
            "mo_columnas": mo_columnas,
            "mo_filas_matriz": mo_filas_matriz,
            "mo_fila_totales": mo_fila_totales,
            "gran_total_mo_pesos": gran_total_mo_pesos,
            "resumen_economico_items": resumen_economico_items,
            "catalogo_mo_todos": catalogo_mo_todos,
            "presupuesto": presupuesto,
        }
    )


def sincronizar_retenida_cable_inventario(apoyo, metros_nuevos):
    """
    Sincroniza los metros de retenida con el material Ítem 43 (Cable para retenida EAR 3/8")
    y descuenta o ajusta automáticamente el stock de bodega en Inventario.
    """
    mat_cable = (
        Material.objects.filter(item="43").first()
        or Material.objects.filter(descripcion__icontains="Cable para retenida EAR 3/8").first()
    )
    if not mat_cable:
        return

    try:
        metros = Decimal(str(metros_nuevos).strip().replace(',', '.')) if metros_nuevos and str(metros_nuevos).strip() else Decimal("0")
    except (ValueError, TypeError, ArithmeticError):
        metros = Decimal("0")

    metros = max(Decimal("0"), metros)
    ap_mat = ApoyoMaterial.objects.filter(apoyo=apoyo, material=mat_cable).first()
    inventario, _ = Inventario.objects.get_or_create(material=mat_cable)

    if ap_mat:
        diferencia = metros - ap_mat.cantidad_requerida
        if diferencia != 0:
            inventario.cantidad -= diferencia
        inventario.save()

        if metros > 0:
            ap_mat.cantidad_requerida = metros
            ap_mat.save()
        else:
            ap_mat.delete()
    elif metros > 0:
        inventario.cantidad -= metros
        inventario.save()

        ApoyoMaterial.objects.create(
            apoyo=apoyo,
            material=mat_cable,
            cantidad_requerida=metros,
            cantidad_retirada=Decimal("0"),
        )

@login_required
@transaction.atomic
def crear_apoyo(request, proyecto_id):
    proyecto = get_object_or_404(
        Proyecto,
        id=proyecto_id
    )

    if request.method == "POST":
        numero_apoyo_val = request.POST.get("numero_apoyo")
        numero_apoyo = int(numero_apoyo_val) if numero_apoyo_val and numero_apoyo_val.isdigit() else None

        fecha_val = request.POST.get("fecha")
        fecha = fecha_val.strip() if fecha_val and fecha_val.strip() else None

        tipo_instalacion = request.POST.get("tipo_instalacion", "").strip()
        direccion = request.POST.get("direccion", "").strip()
        tipo_estructura = request.POST.get("tipo_estructura", "").strip()
        observacion = request.POST.get("observacion", "").strip()
        quien_ejecuta_id = request.POST.get("quien_ejecuta")
        quien_ejecuta_id = int(quien_ejecuta_id) if quien_ejecuta_id and str(quien_ejecuta_id).isdigit() else None

        cant_ret_val = request.POST.get("cantidad_retenida")
        try:
            cantidad_retenida = Decimal(str(cant_ret_val).strip().replace(',', '.')) if cant_ret_val and str(cant_ret_val).strip() else Decimal("0")
        except (ValueError, TypeError, ArithmeticError):
            cantidad_retenida = Decimal("0")

        m_ret_val = request.POST.get("metros_retenido")
        try:
            metros_retenido = Decimal(str(m_ret_val).strip().replace(',', '.')) if m_ret_val and str(m_ret_val).strip() else Decimal("0")
        except (ValueError, TypeError, ArithmeticError):
            metros_retenido = Decimal("0")

        estado_val = request.POST.get("estado", "Pendiente").strip()
        estado = estado_val if estado_val else "Pendiente"

        brazo_val = request.POST.get("brazo", "2").strip()
        brazo = brazo_val if brazo_val else "2"

        apoyo = Apoyo.objects.create(
            proyecto=proyecto,
            quien_ejecuta_id=quien_ejecuta_id,
            numero_apoyo=numero_apoyo,
            nodo=request.POST.get("nodo", "").strip(),
            fecha=fecha,
            tipo_instalacion=tipo_instalacion,
            direccion=direccion,
            tipo_estructura=tipo_estructura,
            cantidad_retenida=cantidad_retenida,
            metros_retenido=metros_retenido,
            brazo=brazo,
            observacion=observacion,
            estado=estado
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

        # Material cable retenida para no duplicarlo si se ingresa manualmente
        mat_cable_obj = (
            Material.objects.filter(item="43").first()
            or Material.objects.filter(descripcion__icontains="Cable para retenida EAR 3/8").first()
        )
        mat_cable_id = mat_cable_obj.id if mat_cable_obj else None

        # Guardar materiales asignados (múltiples)
        materiales_ids = request.POST.getlist("material_id[]")
        cantidades_inst = request.POST.getlist("cantidad_instalada[]") or request.POST.getlist("cantidad[]")
        cantidades_ret = request.POST.getlist("cantidad_retirada[]")

        materiales_creados = 0
        for i, mat_id in enumerate(materiales_ids):
            if not mat_id:
                continue

            # El cable de retenida se gestiona automáticamente por los metros_retenido
            if mat_cable_id and str(mat_id) == str(mat_cable_id):
                continue

            try:
                c_inst_raw = cantidades_inst[i] if i < len(cantidades_inst) else None
                c_ret_raw = cantidades_ret[i] if i < len(cantidades_ret) else None

                c_inst_str = str(c_inst_raw).strip().replace(',', '.') if c_inst_raw is not None else ""
                c_ret_str = str(c_ret_raw).strip().replace(',', '.') if c_ret_raw is not None else ""

                c_inst = Decimal(c_inst_str) if c_inst_str != "" else Decimal("0")
                c_ret = Decimal(c_ret_str) if c_ret_str != "" else Decimal("0")

                if c_inst <= 0 and c_ret <= 0:
                    continue

                inventario, _ = Inventario.objects.get_or_create(material_id=mat_id)
                if c_inst > 0:
                    inventario.cantidad -= c_inst

                if c_ret > 0:
                    inventario.cantidad += c_ret

                inventario.save()

                ApoyoMaterial.objects.create(
                    apoyo=apoyo,
                    material_id=mat_id,
                    cantidad_requerida=max(Decimal("0"), c_inst),
                    cantidad_retirada=max(Decimal("0"), c_ret),
                )
                materiales_creados += 1
            except (ValueError, TypeError, ArithmeticError):
                continue

        # Sincronización automática de Retenidas con Cable EAR 3/8" (Ítem 43) en Bodega
        sincronizar_retenida_cable_inventario(apoyo, metros_retenido)

        # Recalcular Mano de Obra y Presupuesto
        calcular_mano_obra_para_apoyo(apoyo)
        actualizar_presupuesto_proyecto(proyecto)

        messages.success(
            request,
            f"Nodo / Apoyo '{apoyo.nodo or apoyo.numero_apoyo}' creado correctamente con {materiales_creados} material(es) asignado(s)."
        )

        tab = request.POST.get("tab", "materiales").strip()
        url = reverse("detalle_proyecto", kwargs={"id": proyecto.id})
        if tab:
            url += f"?tab={tab}"
        return redirect(url)

    return redirect(
        "detalle_proyecto",
        id=proyecto.id        
    )


@login_required
@transaction.atomic
def editar_apoyo(request, apoyo_id):
    apoyo = get_object_or_404(
        Apoyo.objects.select_related("proyecto"),
        id=apoyo_id
    )
    proyecto = apoyo.proyecto

    if request.method == "POST":
        numero_apoyo_val = request.POST.get("numero_apoyo")
        apoyo.numero_apoyo = int(numero_apoyo_val) if numero_apoyo_val and numero_apoyo_val.isdigit() else None

        fecha_val = request.POST.get("fecha")
        apoyo.fecha = fecha_val.strip() if fecha_val and fecha_val.strip() else None

        apoyo.nodo = request.POST.get("nodo", "").strip()
        apoyo.brazo = request.POST.get("brazo", "2").strip() or "2"
        apoyo.tipo_instalacion = request.POST.get("tipo_instalacion", "").strip()
        apoyo.direccion = request.POST.get("direccion", "").strip()
        apoyo.tipo_estructura = request.POST.get("tipo_estructura", "").strip()
        apoyo.observacion = request.POST.get("observacion", "").strip()
        
        estado_val = request.POST.get("estado", apoyo.estado or "Pendiente").strip()
        apoyo.estado = estado_val if estado_val else "Pendiente"

        quien_ejecuta_id = request.POST.get("quien_ejecuta")
        apoyo.quien_ejecuta_id = int(quien_ejecuta_id) if quien_ejecuta_id and str(quien_ejecuta_id).isdigit() else None

        cant_ret_val = request.POST.get("cantidad_retenida")
        try:
            apoyo.cantidad_retenida = Decimal(str(cant_ret_val).strip().replace(',', '.')) if cant_ret_val and str(cant_ret_val).strip() else Decimal("0")
        except (ValueError, TypeError, ArithmeticError):
            apoyo.cantidad_retenida = Decimal("0")

        m_ret_val = request.POST.get("metros_retenido")
        try:
            apoyo.metros_retenido = Decimal(str(m_ret_val).strip().replace(',', '.')) if m_ret_val and str(m_ret_val).strip() else Decimal("0")
        except (ValueError, TypeError, ArithmeticError):
            apoyo.metros_retenido = Decimal("0")

        apoyo.save()

        # Actualizar Luminarias
        apoyo.luminarias.all().delete()
        potencias = request.POST.getlist("potencia[]")
        codigos = request.POST.getlist("codigo_luminaria[]")
        for potencia, codigo in zip(potencias, codigos):
            if potencia.strip() or codigo.strip():
                ApoyoLuminaria.objects.create(
                    apoyo=apoyo,
                    potencia=potencia.strip(),
                    codigo=codigo.strip()
                )

        # Material cable retenida para no duplicarlo si se ingresa manualmente
        mat_cable_obj = (
            Material.objects.filter(item="43").first()
            or Material.objects.filter(descripcion__icontains="Cable para retenida EAR 3/8").first()
        )
        mat_cable_id = mat_cable_obj.id if mat_cable_obj else None

        # Sincronizar Materiales
        materiales_ids = request.POST.getlist("material_id[]")
        cantidades_inst = request.POST.getlist("cantidad_instalada[]") or request.POST.getlist("cantidad[]")
        cantidades_ret = request.POST.getlist("cantidad_retirada[]")

        materiales_actuales = {am.material_id: am for am in apoyo.materiales.all()}
        materiales_nuevos_procesados = set()

        for i, mat_id in enumerate(materiales_ids):
            if not mat_id or not str(mat_id).isdigit():
                continue
            mat_id_int = int(mat_id)

            # El cable de retenida se gestiona automáticamente por los metros_retenido
            if mat_cable_id and mat_id_int == mat_cable_id:
                continue

            try:
                c_inst_raw = cantidades_inst[i] if i < len(cantidades_inst) else None
                c_ret_raw = cantidades_ret[i] if i < len(cantidades_ret) else None

                c_inst_str = str(c_inst_raw).strip().replace(',', '.') if c_inst_raw is not None else ""
                c_ret_str = str(c_ret_raw).strip().replace(',', '.') if c_ret_raw is not None else ""

                c_inst = Decimal(c_inst_str) if c_inst_str != "" else Decimal("0")
                c_ret = Decimal(c_ret_str) if c_ret_str != "" else Decimal("0")

                if c_inst <= 0 and c_ret <= 0:
                    continue

                inventario, _ = Inventario.objects.get_or_create(material_id=mat_id_int)

                if mat_id_int in materiales_actuales:
                    am = materiales_actuales[mat_id_int]
                    diferencia = c_inst - am.cantidad_requerida
                    if diferencia != 0:
                        inventario.cantidad -= diferencia

                    diferencia_ret = c_ret - am.cantidad_retirada
                    if diferencia_ret != 0:
                        inventario.cantidad += diferencia_ret

                    inventario.save()

                    am.cantidad_requerida = max(Decimal("0"), c_inst)
                    am.cantidad_retirada = max(Decimal("0"), c_ret)
                    am.save()
                else:
                    if c_inst > 0:
                        inventario.cantidad -= c_inst

                    if c_ret > 0:
                        inventario.cantidad += c_ret

                    inventario.save()

                    ApoyoMaterial.objects.create(
                        apoyo=apoyo,
                        material_id=mat_id_int,
                        cantidad_requerida=max(Decimal("0"), c_inst),
                        cantidad_retirada=max(Decimal("0"), c_ret),
                    )

                materiales_nuevos_procesados.add(mat_id_int)
            except (ValueError, TypeError, ArithmeticError):
                continue

        # Eliminar materiales que se hayan removido (excepto el cable de retenida que se sincroniza aparte)
        for mat_id_antiguo, am in materiales_actuales.items():
            if mat_cable_id and mat_id_antiguo == mat_cable_id:
                continue
            if mat_id_antiguo not in materiales_nuevos_procesados:
                inv_del, _ = Inventario.objects.get_or_create(material_id=mat_id_antiguo)
                if am.cantidad_requerida > 0:
                    inv_del.cantidad += am.cantidad_requerida
                if am.cantidad_retirada > 0:
                    inv_del.cantidad -= am.cantidad_retirada
                inv_del.save()
                am.delete()

        # Sincronización automática de Retenidas con Cable EAR 3/8" (Ítem 43) en Bodega
        sincronizar_retenida_cable_inventario(apoyo, apoyo.metros_retenido)

        # Recalcular Mano de Obra y Presupuesto
        calcular_mano_obra_para_apoyo(apoyo)
        actualizar_presupuesto_proyecto(proyecto)

        messages.success(
            request,
            f"Nodo / Apoyo '{apoyo.nodo or apoyo.numero_apoyo}' actualizado correctamente."
        )

        tab = request.POST.get("tab", "materiales").strip()
        url = reverse("detalle_proyecto", kwargs={"id": proyecto.id})
        if tab:
            url += f"?tab={tab}"
        return redirect(url)

    return redirect("detalle_proyecto", id=proyecto.id)


@login_required
@transaction.atomic
def despachar_bodega_apoyo(request, apoyo_id):
    apoyo = get_object_or_404(
        Apoyo.objects.select_related("proyecto", "quien_ejecuta"),
        id=apoyo_id
    )
    proyecto = apoyo.proyecto

    is_ajax = (
        request.headers.get("x-requested-with") == "XMLHttpRequest"
        or request.POST.get("ajax") == "1"
        or "application/json" in request.headers.get("Accept", "")
    )

    if request.method == "POST":
        material_id = request.POST.get("material_id")
        cantidad_str = request.POST.get("cantidad", "0")

        if not material_id:
            if is_ajax:
                return JsonResponse({"success": False, "error": "Selecciona un material de bodega válido."}, status=400)
            return redirect("detalle_proyecto", id=proyecto.id)

        try:
            cant = Decimal(str(cantidad_str).strip().replace(',', '.'))
            if cant <= 0:
                if is_ajax:
                    return JsonResponse({"success": False, "error": "La cantidad debe ser un número mayor a cero."}, status=400)
                return redirect("detalle_proyecto", id=proyecto.id)
        except (ValueError, TypeError, ArithmeticError):
            if is_ajax:
                return JsonResponse({"success": False, "error": "La cantidad ingresada no es válida."}, status=400)
            return redirect("detalle_proyecto", id=proyecto.id)

        material = get_object_or_404(Material, id=material_id)
        inventario, _ = Inventario.objects.get_or_create(material=material)
        stock_previo = inventario.cantidad or Decimal("0")
        unidad_str = material.unidad or "UN"

        # Descontar del inventario general de bodega (permite negativos para reflejar déficit en bodega)
        inventario.cantidad -= cant
        inventario.save()

        warning_msg = None
        if inventario.cantidad < 0:
            warning_msg = f"⚠️ Advertencia: Stock en déficit en Bodega Central para '{material.descripcion}'. Quedó en {float(inventario.cantidad):g} {unidad_str} (se despacharon {float(cant):g} {unidad_str} al poste)."
            if not is_ajax:
                messages.warning(request, warning_msg)
        else:
            if not is_ajax:
                messages.success(
                    request,
                    f"Se despacharon exitosamente {float(cant):g} {unidad_str} de '{material.descripcion}' desde Bodega Central al poste (Stock restante en bodega: {float(inventario.cantidad):g} {unidad_str})."
                )

        # Registrar en Historial / Kardex de Bodega Central
        nodo_str = apoyo.nodo or str(apoyo.numero_apoyo or "Poste")
        obs_user = request.POST.get("observacion", "").strip()
        registrar_movimiento_inventario(
            material=material,
            tipo_movimiento=MovimientoInventario.Tipos.DESPACHO,
            cantidad=-cant,
            stock_anterior=stock_previo,
            stock_resultante=inventario.cantidad,
            usuario=request.user,
            proyecto=proyecto,
            apoyo=apoyo,
            detalle_origen_destino=f"Proyecto {proyecto.numero_emcali} • Poste/Nodo {nodo_str}",
            observacion=obs_user or f"Despacho directo desde Bodega al poste/nodo {nodo_str}"
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

        calcular_mano_obra_para_apoyo(apoyo)
        actualizar_presupuesto_proyecto(proyecto)

        if is_ajax:
            return JsonResponse({
                "success": True,
                "message": f"Se despacharon {float(cant):g} {unidad_str} de '{material.descripcion}' al poste.",
                "warning": warning_msg,
                "material_id": material.id,
                "material_item": material.item,
                "material_descripcion": material.descripcion,
                "unidad": unidad_str,
                "cantidad_despachada": float(cant),
                "cantidad_total_instalada": float(apoyo_mat.cantidad_requerida),
                "cantidad_retirada": float(apoyo_mat.cantidad_retirada),
                "stock_restante": float(inventario.cantidad),
            })

        tab = request.POST.get("tab", "materiales").strip()
        url = reverse("detalle_proyecto", kwargs={"id": proyecto.id})
        if tab:
            url += f"?tab={tab}"
        return redirect(url)

    return redirect("detalle_proyecto", id=proyecto.id)


@login_required
def detalle_apoyo(request, apoyo_id):
    """
    Redirecciona de forma unificada a la vista principal de ingeniería del proyecto
    abriendo directamente el modal de edición del poste seleccionado.
    Esto unifica la interfaz y evita duplicidad o interferencia entre dos editores.
    """
    apoyo = get_object_or_404(
        Apoyo.objects.select_related("proyecto"),
        id=apoyo_id
    )
    url = reverse("detalle_proyecto", kwargs={"id": apoyo.proyecto.id})
    return redirect(f"{url}?tab=materiales&editar_apoyo={apoyo.id}")

@login_required
@transaction.atomic
def eliminar_apoyo(request, apoyo_id):
    apoyo = Apoyo.objects.filter(id=apoyo_id).first()
    if not apoyo:
        messages.warning(request, "El poste o nodo que intentas eliminar ya no existe o fue removido previamente.")
        return redirect("lista_proyectos")

    proyecto = apoyo.proyecto
    nodo_nombre = apoyo.nodo or str(apoyo.numero_apoyo or "Poste")
    tab = request.POST.get("tab", "materiales")

    if request.method == "POST":
        # Devolver materiales asignados a la bodega central
        for am in apoyo.materiales.all():
            if am.cantidad_requerida > 0:
                inventario, _ = Inventario.objects.get_or_create(material=am.material)
                inventario.cantidad += am.cantidad_requerida
                inventario.save()

        apoyo.delete()
        if proyecto:
            actualizar_presupuesto_proyecto(proyecto)
        messages.success(request, f"Poste / Nodo '{nodo_nombre}' eliminado correctamente del proyecto.")

    if proyecto:
        return redirect(f"/ingenieria/proyectos/{proyecto.id}/?tab={tab}")
    return redirect("lista_proyectos")


@login_required
@transaction.atomic
def agregar_material_apoyo_rapido(request, apoyo_id):
    """
    Agrega un material a un poste directamente desde la vista del proyecto (modal rápido),
    descontando existencias de bodega y recalculando la mano de obra y presupuesto.
    """
    apoyo = get_object_or_404(Apoyo, id=apoyo_id)
    tab = request.POST.get("tab", "mano_obra")

    if request.method == "POST":
        material_id = request.POST.get("material_id")
        cant_inst_str = request.POST.get("cantidad_instalada", "0").strip().replace(',', '.')
        cant_ret_str = request.POST.get("cantidad_retirada", "0").strip().replace(',', '.')

        try:
            cant_inst = Decimal(cant_inst_str) if cant_inst_str else Decimal("0")
            cant_ret = Decimal(cant_ret_str) if cant_ret_str else Decimal("0")

            if material_id and (cant_inst > 0 or cant_ret > 0):
                material = get_object_or_404(Material, id=material_id)
                inventario, _ = Inventario.objects.get_or_create(material=material)
                stock_previo = inventario.cantidad or Decimal("0")
                nodo_str = apoyo.nodo or str(apoyo.numero_apoyo or "Poste")
                proy_emcali = apoyo.proyecto.numero_emcali if apoyo.proyecto else ""

                if cant_inst > 0:
                    inventario.cantidad -= cant_inst
                    if inventario.cantidad < 0:
                        messages.warning(
                            request,
                            f"⚠️ Advertencia: Stock en déficit en bodega para '{material.descripcion}' (Stock actual: {float(inventario.cantidad):g} {material.unidad or 'UN'}). Se asignaron {float(cant_inst):g} al poste."
                        )
                    registrar_movimiento_inventario(
                        material=material,
                        tipo_movimiento=MovimientoInventario.Tipos.DESPACHO,
                        cantidad=-cant_inst,
                        stock_anterior=stock_previo,
                        stock_resultante=inventario.cantidad,
                        usuario=request.user,
                        proyecto=apoyo.proyecto,
                        apoyo=apoyo,
                        detalle_origen_destino=f"Proyecto {proy_emcali} • Poste {nodo_str}",
                        observacion=f"Asignación rápida al poste {nodo_str}"
                    )

                if cant_ret > 0:
                    stock_antes_ret = inventario.cantidad
                    inventario.cantidad += cant_ret
                    registrar_movimiento_inventario(
                        material=material,
                        tipo_movimiento=MovimientoInventario.Tipos.DEVOLUCION,
                        cantidad=cant_ret,
                        stock_anterior=stock_antes_ret,
                        stock_resultante=inventario.cantidad,
                        usuario=request.user,
                        proyecto=apoyo.proyecto,
                        apoyo=apoyo,
                        detalle_origen_destino=f"Proyecto {proy_emcali} • Poste {nodo_str}",
                        observacion=f"Material retirado/desmontado en poste {nodo_str}"
                    )

                inventario.save()

                apoyo_mat, created = ApoyoMaterial.objects.get_or_create(
                    apoyo=apoyo,
                    material=material,
                    defaults={"cantidad_requerida": cant_inst, "cantidad_retirada": cant_ret}
                )
                if not created:
                    apoyo_mat.cantidad_requerida += cant_inst
                    apoyo_mat.cantidad_retirada += cant_ret
                    apoyo_mat.save()

                calcular_mano_obra_para_apoyo(apoyo)
                actualizar_presupuesto_proyecto(apoyo.proyecto)
                messages.success(request, f"Material '{material.descripcion}' agregado al poste {apoyo.nodo or apoyo.numero_apoyo}.")
        except Exception as e:
            messages.error(request, f"Error al agregar material: {e}")

    return redirect(f"/ingenieria/proyectos/{apoyo.proyecto.id}/?tab={tab}")


@login_required
@transaction.atomic
def editar_material_apoyo_rapido(request, apoyo_id):
    """
    Edita las cantidades instaladas/retiradas de un material existente en un poste desde el modal rápido,
    ajustando inventario y recalculando la mano de obra y presupuesto.
    """
    apoyo = get_object_or_404(Apoyo, id=apoyo_id)
    tab = request.POST.get("tab", "mano_obra")

    if request.method == "POST":
        am_id = request.POST.get("apoyo_material_id")
        cant_inst_str = request.POST.get("cantidad_instalada", "0").strip().replace(',', '.')
        cant_ret_str = request.POST.get("cantidad_retirada", "0").strip().replace(',', '.')

        try:
            cant_inst = Decimal(cant_inst_str) if cant_inst_str else Decimal("0")
            cant_ret = Decimal(cant_ret_str) if cant_ret_str else Decimal("0")

            apoyo_mat = get_object_or_404(ApoyoMaterial, id=am_id, apoyo=apoyo)
            inventario, _ = Inventario.objects.get_or_create(material=apoyo_mat.material)
            stock_ant = inventario.cantidad or Decimal("0")
            nodo_str = apoyo.nodo or str(apoyo.numero_apoyo or "Poste")
            proy_emcali = apoyo.proyecto.numero_emcali if apoyo.proyecto else ""

            diferencia = cant_inst - apoyo_mat.cantidad_requerida
            if diferencia != 0:
                inventario.cantidad -= diferencia
                registrar_movimiento_inventario(
                    material=apoyo_mat.material,
                    tipo_movimiento=MovimientoInventario.Tipos.DESPACHO if diferencia > 0 else MovimientoInventario.Tipos.DEVOLUCION,
                    cantidad=-diferencia,
                    stock_anterior=stock_ant,
                    stock_resultante=inventario.cantidad,
                    usuario=request.user,
                    proyecto=apoyo.proyecto,
                    apoyo=apoyo,
                    detalle_origen_destino=f"Proyecto {proy_emcali} • Poste {nodo_str}",
                    observacion=f"Ajuste en poste {nodo_str}: variación de {'instalado' if diferencia > 0 else 'reintegrado'} {abs(float(diferencia)):g} {apoyo_mat.material.unidad or 'UN'}"
                )
                stock_ant = inventario.cantidad

            diferencia_ret = cant_ret - apoyo_mat.cantidad_retirada
            if diferencia_ret != 0:
                inventario.cantidad += diferencia_ret
                registrar_movimiento_inventario(
                    material=apoyo_mat.material,
                    tipo_movimiento=MovimientoInventario.Tipos.DEVOLUCION if diferencia_ret > 0 else MovimientoInventario.Tipos.DESPACHO,
                    cantidad=diferencia_ret,
                    stock_anterior=stock_ant,
                    stock_resultante=inventario.cantidad,
                    usuario=request.user,
                    proyecto=apoyo.proyecto,
                    apoyo=apoyo,
                    detalle_origen_destino=f"Proyecto {proy_emcali} • Poste {nodo_str}",
                    observacion=f"Ajuste de retiro en poste {nodo_str}: {abs(float(diferencia_ret)):g} {apoyo_mat.material.unidad or 'UN'}"
                )

            inventario.save()

            apoyo_mat.cantidad_requerida = max(Decimal("0"), cant_inst)
            apoyo_mat.cantidad_retirada = max(Decimal("0"), cant_ret)
            apoyo_mat.save()

            calcular_mano_obra_para_apoyo(apoyo)
            actualizar_presupuesto_proyecto(apoyo.proyecto)
            messages.success(request, f"Cantidades actualizadas para '{apoyo_mat.material.descripcion}' en el poste {apoyo.nodo or apoyo.numero_apoyo}.")
        except Exception as e:
            messages.error(request, f"Error al actualizar material: {e}")

    return redirect(f"/ingenieria/proyectos/{apoyo.proyecto.id}/?tab={tab}")


@login_required
@transaction.atomic
def eliminar_material_apoyo_rapido(request, apoyo_material_id):
    """
    Elimina un material de un poste, devuelve lo instalado a la bodega central y recalcula la mano de obra.
    """
    apoyo_mat = ApoyoMaterial.objects.filter(id=apoyo_material_id).first()
    if not apoyo_mat:
        messages.warning(request, "El material seleccionado ya no existe en el poste.")
        return redirect("lista_proyectos")

    apoyo = apoyo_mat.apoyo
    proyecto = apoyo.proyecto if apoyo else None
    tab = request.POST.get("tab", "mano_obra")

    if request.method == "POST":
        nombre_mat = apoyo_mat.material.descripcion if apoyo_mat.material else "Material"
        if apoyo_mat.material:
            inv_del, _ = Inventario.objects.get_or_create(material=apoyo_mat.material)
            stock_ant = inv_del.cantidad or Decimal("0")
            if apoyo_mat.cantidad_requerida > 0:
                inv_del.cantidad += apoyo_mat.cantidad_requerida
            if apoyo_mat.cantidad_retirada > 0:
                inv_del.cantidad -= apoyo_mat.cantidad_retirada
            inv_del.save()

            if apoyo_mat.cantidad_requerida > 0:
                nodo_str = apoyo.nodo or str(apoyo.numero_apoyo or "Poste") if apoyo else ""
                proy_str = apoyo.proyecto.numero_emcali if (apoyo and apoyo.proyecto) else ""
                registrar_movimiento_inventario(
                    material=apoyo_mat.material,
                    tipo_movimiento=MovimientoInventario.Tipos.DEVOLUCION,
                    cantidad=apoyo_mat.cantidad_requerida,
                    stock_anterior=stock_ant,
                    stock_resultante=inv_del.cantidad,
                    usuario=request.user,
                    proyecto=apoyo.proyecto if apoyo else None,
                    apoyo=apoyo,
                    detalle_origen_destino=f"Proyecto {proy_str} • Poste {nodo_str}",
                    observacion=f"Material removido del poste {nodo_str}: se devolvió a bodega"
                )

        apoyo_mat.delete()
        if apoyo:
            calcular_mano_obra_para_apoyo(apoyo)
        if proyecto:
            actualizar_presupuesto_proyecto(proyecto)
        messages.success(request, f"Material '{nombre_mat}' eliminado del poste {apoyo.nodo or apoyo.numero_apoyo if apoyo else ''}.")

    if proyecto:
        return redirect(f"/ingenieria/proyectos/{proyecto.id}/?tab={tab}")
    return redirect("lista_proyectos")



@login_required
def exportar_materiales_proyecto_excel(request, proyecto_id):
    """
    Delega la exportación al exportador unificado de proyectos (con Matriz de Balance, Requeridos, Devolución y Nodos).
    """
    from core.views.logistica.proyectos_materiales import exportar_materiales_proyecto_excel as exportar_full
    return exportar_full(request, proyecto_id)


@login_required
def imprimir_formato_poste_a_poste(request, proyecto_id):
    """
    Genera y descarga el archivo oficial de terreno Poste a Poste (AP o MT)
    detectando automáticamente el tipo de proyecto.
    Llena únicamente los datos iniciales de trabajo (NODO, POTENCIA, BRAZO)
    y deja las demás columnas en blanco para que el personal en terreno anote a mano.
    """
    proyecto = get_object_or_404(
        Proyecto.objects.select_related("macroproyecto"),
        id=proyecto_id
    )
    apoyos = Apoyo.objects.filter(proyecto=proyecto).prefetch_related("luminarias").order_by("numero_apoyo", "id")

    es_mt = (proyecto.tipo == Proyecto.Tipos.MT)
    plantillas_dir = os.path.join(settings.BASE_DIR, "plantillas_excel")

    if es_mt:
        # ==========================================
        # FORMATO MEDIA TENSIÓN (MT)
        # ==========================================
        plantilla_path = os.path.join(plantillas_dir, "PLANTILLA_POSTE_A_POSTE_MT.xlsx")
        if not os.path.exists(plantilla_path):
            plantilla_path = os.path.join(plantillas_dir, "POSTE_A_POSTE_MT.xlsx")

        wb = openpyxl.load_workbook(plantilla_path)
        sheet = wb.active

        # Encabezado MT (Fecha y Circuito; la Dirección se deja en blanco para diligenciamiento en terreno)
        sheet.cell(8, 1).value = f"FECHA: {timezone.now().strftime('%d-%m-%Y')}"
        sheet.cell(8, 9).value = f"CIRCUITO: {proyecto.numero_emcali or ''}"

        # En MT, los números 1, 2, 3, 4... de la fila 10 bajo 'POSTE' son los identificadores de la plantilla y no se modifican

        # Ajuste de impresión MT: encajar en 1 sola hoja Oficio / Legal
        sheet.page_setup.orientation = sheet.ORIENTATION_PORTRAIT
        sheet.page_setup.paperSize = 5  # Papel Oficio / Legal
        sheet.sheet_properties.pageSetUpPr.fitToPage = True
        sheet.page_setup.fitToWidth = 1
        sheet.page_setup.fitToHeight = 1
        sheet.page_setup.scale = None
        sheet.print_area = f"'{sheet.title}'!$A$1:$Z$77"

        filename = f"POSTE_A_POSTE_MT_{proyecto.numero_emcali}.xlsx"
    else:
        # ==========================================
        # FORMATO ALUMBRADO PÚBLICO (AP / BARRIO / PARQUE)
        # ==========================================
        plantilla_path = os.path.join(plantillas_dir, "PLANTILLA_POSTE_A_POSTE_AP.xlsx")
        if not os.path.exists(plantilla_path):
            plantilla_path = os.path.join(plantillas_dir, "POSTE_A_POSTE_AP.xlsx")

        wb = openpyxl.load_workbook(plantilla_path)
        sheet = wb.active

        # Encabezado AP (Fila 7: Microproyecto y Fecha; Dirección se conserva en blanco para cada nodo)
        # T7: Microproyecto
        sheet.cell(7, 20).value = proyecto.numero_emcali
        # Y7: Fecha
        sheet.cell(7, 25).value = f"FECHA: {timezone.now().strftime('%d-%m-%Y')}"

        thin_border = Border(
            left=Side(style='thin', color='A0A0A0'),
            right=Side(style='thin', color='A0A0A0'),
            top=Side(style='thin', color='A0A0A0'),
            bottom=Side(style='thin', color='A0A0A0')
        )
        font_consecutivo = Font(name="Arial", size=11, bold=False)
        font_nodo = Font(name="Arial", size=14, bold=True)
        font_potencia = Font(name="Arial", size=11, bold=True)
        font_brazo = Font(name="Arial", size=11, bold=True)
        font_celda = Font(name="Arial", size=10, bold=False)
        align_center = Alignment(horizontal="center", vertical="center")

        # Llenar nodos desde la fila 12
        for idx, apoyo in enumerate(apoyos):
            r = 12 + idx

            # Respetar y asegurar las medidas exactas de fila de la plantilla original para que quepan en 1 hoja
            if sheet.row_dimensions[r].height is None or sheet.row_dimensions[r].height < 20:
                sheet.row_dimensions[r].height = 58.5 if r <= 21 else (49.5 if r <= 28 else 51.0)

            for c in range(1, 52):
                cell = sheet.cell(r, c)
                cell.border = thin_border
                cell.font = font_celda
                cell.alignment = align_center

            # Col 1: Consecutivo
            c1 = sheet.cell(r, 1)
            c1.value = idx + 1
            c1.font = font_consecutivo

            # Col 3: NODO (Arial 14 Bold, grande y legible para los trabajadores en terreno)
            c3 = sheet.cell(r, 3)
            c3.value = apoyo.nodo or apoyo.numero_apoyo or ""
            c3.font = font_nodo

            # Col 4: POT.INST (Arial 11 Bold)
            lum = apoyo.luminarias.first()
            c4 = sheet.cell(r, 4)
            c4.value = lum.potencia if lum else ""
            c4.font = font_potencia

            # Col 5: BRAZO INSTA (Arial 11 Bold)
            c5 = sheet.cell(r, 5)
            c5.value = apoyo.brazo or "2"
            c5.font = font_brazo

            # Cols 6..51: quedan vacías para llenado en terreno

        # Ajuste de impresión para que encaje exactamente en 1 sola hoja de oficio (Legal) apaisada
        sheet.page_setup.orientation = sheet.ORIENTATION_LANDSCAPE
        sheet.page_setup.paperSize = 5  # Oficio / Legal (8.5 x 14 pulg)
        sheet.sheet_properties.pageSetUpPr.fitToPage = True
        sheet.page_setup.fitToWidth = 1
        sheet.page_setup.fitToHeight = 1
        sheet.page_setup.scale = None

        sheet.page_margins.left = 0.0
        sheet.page_margins.right = 0.0
        sheet.page_margins.top = 0.0
        sheet.page_margins.bottom = 0.0
        sheet.page_margins.header = 0.0
        sheet.page_margins.footer = 0.0

        max_row_impresion = max(41, 11 + len(apoyos))
        sheet.print_area = f"'{sheet.title}'!$A$2:$AZ${max_row_impresion}"

        filename = f"POSTE_A_POSTE_AP_{proyecto.numero_emcali}.xlsx"

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response




# ==============================================================================
# 🛠️ VISTAS DE MANO DE OBRA Y LIQUIDACIÓN AUTOMÁTICA (INGENIERÍA)
# ==============================================================================

@login_required
def ejecutar_calculo_mano_obra(request, proyecto_id):
    """
    Ejecuta el motor de reglas automáticas para todos los apoyos del proyecto.
    """
    proyecto = Proyecto.objects.filter(id=proyecto_id).first()
    if not proyecto:
        messages.warning(request, "El proyecto indicado ya no existe.")
        return redirect("lista_proyectos")

    if request.method == "POST":
        total_creados = calcular_mano_obra_proyecto_completo(proyecto, preservar_manuales=True)
        messages.success(
            request,
            f"⚡ Mano de Obra calculada exitosamente para el Proyecto {proyecto.numero_emcali}. Se actualizaron {total_creados} asignaciones de actividades."
        )
    return redirect(f"/ingenieria/proyectos/{proyecto.id}/?tab=mano_obra")


@login_required
@transaction.atomic
def guardar_mano_obra_manual(request, apoyo_id):
    """
    Permite agregar o editar múltiples actividades de mano de obra manuales en un apoyo.
    Soporta asignación múltiple (listas de item_mano_obra_id[], cantidad[], observacion[]).
    """
    apoyo = Apoyo.objects.filter(id=apoyo_id).first()
    if not apoyo:
        messages.warning(request, "El poste o apoyo seleccionado ya no existe.")
        return redirect("lista_proyectos")

    if request.method == "POST":
        # Puede recibir arrays (item_mano_obra_id[], cantidad[], observacion[]) o valores individuales
        items_ids = request.POST.getlist("item_mano_obra_id[]")
        if not items_ids:
            items_ids = request.POST.getlist("item_mano_obra_id")

        cantidades = request.POST.getlist("cantidad[]")
        if not cantidades:
            cantidades = request.POST.getlist("cantidad")

        observaciones = request.POST.getlist("observacion[]")
        if not observaciones:
            observaciones = request.POST.getlist("observacion")

        # Si viene un solo valor escalar sin listas
        if not items_ids and request.POST.get("item_mano_obra_id"):
            items_ids = [request.POST.get("item_mano_obra_id")]
            cantidades = [request.POST.get("cantidad", "0")]
            observaciones = [request.POST.get("observacion", "")]

        guardados_count = 0
        removidos_count = 0

        try:
            for idx, item_id in enumerate(items_ids):
                if not item_id:
                    continue

                cant_str = cantidades[idx].strip().replace(',', '.') if idx < len(cantidades) else "0"
                obs = observaciones[idx].strip() if idx < len(observaciones) else ""

                try:
                    cantidad = Decimal(cant_str) if cant_str else Decimal("0")
                except Exception:
                    continue

                item = ItemManoObra.objects.filter(id=item_id).first()
                if not item:
                    continue

                if cantidad > 0:
                    amo, _ = ApoyoManoObra.objects.get_or_create(
                        apoyo=apoyo,
                        item_mano_obra=item,
                        defaults={"cantidad": cantidad, "origen": ApoyoManoObra.Origen.MANUAL, "observacion": obs}
                    )
                    amo.cantidad = cantidad
                    amo.origen = ApoyoManoObra.Origen.MANUAL
                    amo.observacion = obs
                    amo.save()
                    guardados_count += 1
                else:
                    deleted, _ = ApoyoManoObra.objects.filter(apoyo=apoyo, item_mano_obra=item).delete()
                    if deleted:
                        removidos_count += 1

            if guardados_count > 0 or removidos_count > 0:
                msg_part = f"Se actualizaron {guardados_count} servicio(s) manual(es)"
                if removidos_count > 0:
                    msg_part += f" y se removieron {removidos_count}"
                messages.success(
                    request,
                    f"✅ {msg_part} en el poste {apoyo.nodo or apoyo.numero_apoyo}."
                )
            else:
                messages.info(request, "No se registraron cambios en los servicios manuales.")

            if apoyo.proyecto:
                actualizar_presupuesto_proyecto(apoyo.proyecto)
        except Exception as e:
            messages.error(request, f"Error al guardar actividades manuales: {e}")

    if apoyo.proyecto:
        return redirect(f"/ingenieria/proyectos/{apoyo.proyecto.id}/?tab=mano_obra")
    return redirect("lista_proyectos")


@login_required
@transaction.atomic
def eliminar_mano_obra_apoyo(request, amo_id):
    """
    Elimina una asignación de mano de obra de un apoyo.
    """
    amo = ApoyoManoObra.objects.filter(id=amo_id).first()
    if not amo:
        messages.warning(request, "La actividad de mano de obra seleccionada ya no existe.")
        return redirect("lista_proyectos")

    proyecto = amo.apoyo.proyecto if (amo.apoyo and amo.apoyo.proyecto) else None
    if request.method == "POST":
        desc = amo.item_mano_obra.descripcion if amo.item_mano_obra else "Actividad"
        amo.delete()
        if proyecto:
            actualizar_presupuesto_proyecto(proyecto)
        messages.success(request, f"Actividad '{desc}' eliminada correctamente.")

    if proyecto:
        return redirect(f"/ingenieria/proyectos/{proyecto.id}/?tab=mano_obra")
    return redirect("lista_proyectos")


@login_required
def catalogo_mano_obra(request):
    """
    Lista administrativa de las 128 actividades de Mano de Obra y tarifas.
    """
    query = request.GET.get("q", "").strip()
    categoria_sel = request.GET.get("categoria", "").strip()

    items = ItemManoObra.objects.all()
    if query:
        items = items.filter(
            Q(codigo__icontains=query) |
            Q(descripcion__icontains=query)
        )
    if categoria_sel:
        items = items.filter(categoria=categoria_sel)

    items = items.order_by("codigo")
    categorias = ItemManoObra.Categorias.choices

    return render(
        request,
        "ingenieria/mano_obra/catalogo.html",
        {
            "items": items,
            "categorias": categorias,
            "query": query,
            "categoria_sel": categoria_sel,
            "total_items": ItemManoObra.objects.count(),
            "total_filtrados": items.count(),
        }
    )


@login_required
def editar_tarifa_mano_obra(request, item_id):
    """
    Actualiza el precio unitario contractual de una actividad.
    """
    item = get_object_or_404(ItemManoObra, id=item_id)
    if request.method == "POST":
        precio_str = request.POST.get("valor_unitario", "0").strip().replace(',', '.')
        try:
            nuevo_precio = Decimal(precio_str)
            item.valor_unitario = max(Decimal("0"), nuevo_precio)
            item.save()
            messages.success(request, f"Tarifa actualizada para '{item.descripcion}': ${item.valor_unitario:,.2f}")
        except Exception as e:
            messages.error(request, f"Error al actualizar tarifa: {e}")

    return redirect("catalogo_mano_obra")


@login_required
def exportar_liquidacion_proyecto_excel(request, proyecto_id):
    """
    Exporta la liquidación completa del proyecto (Materiales, Mano de Obra y Resumen Económico)
    en formato Excel oficial idéntico a proyecciones.xlsx.
    """
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    apoyos = Apoyo.objects.filter(proyecto=proyecto).order_by("numero_apoyo", "id")

    # Crear libro de Excel
    wb = openpyxl.Workbook()
    
    # 1. HOJA RESUMEN
    ws_resumen = wb.active
    ws_resumen.title = "RESUMEN"

    # Encabezados de estilo
    font_bold = Font(name="Calibri", size=11, bold=True)
    font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    fill_header = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    fill_sub = PatternFill(start_color="3B82F6", end_color="3B82F6", fill_type="solid")
    border_thin = Border(
        left=Side(style='thin', color='D1D5DB'),
        right=Side(style='thin', color='D1D5DB'),
        top=Side(style='thin', color='D1D5DB'),
        bottom=Side(style='thin', color='D1D5DB')
    )

    ws_resumen.append(["", proyecto.etiqueta.upper(), proyecto.numero_emcali, "", "FECHA", timezone.now().strftime("%d/%m/%Y")])
    ws_resumen.append([])
    ws_resumen.append(["ITEM", "DESCRIPCIÓN DE ACTIVIDAD / SERVICIO", "CÓDIGO", "UND", "CANTIDAD", "VALOR UNITARIO", "VALOR TOTAL"])

    for col in range(1, 8):
        cell = ws_resumen.cell(row=3, column=col)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # Obtener todas las manos de obra calculadas
    apoyos_ids = apoyos.values_list('id', flat=True)
    amos = ApoyoManoObra.objects.filter(apoyo_id__in=apoyos_ids).select_related('item_mano_obra')
    
    totales_por_item = {}
    for amo in amos:
        totales_por_item[amo.item_mano_obra] = totales_por_item.get(amo.item_mano_obra, Decimal("0")) + amo.cantidad

    r_idx = 4
    grand_total_mo = Decimal("0")
    for item, cant in sorted(totales_por_item.items(), key=lambda x: x[0].codigo):
        if cant > 0:
            v_total = cant * item.valor_unitario
            grand_total_mo += v_total
            ws_resumen.append([
                r_idx - 3,
                item.descripcion,
                item.codigo,
                item.unidad,
                float(cant),
                float(item.valor_unitario),
                float(v_total)
            ])
            for c_i in range(1, 8):
                ws_resumen.cell(row=r_idx, column=c_i).border = border_thin
            r_idx += 1

    # Fila total
    ws_resumen.append(["", "TOTAL MANO DE OBRA Y SERVICIOS", "", "", "", "", float(grand_total_mo)])
    for c_i in range(1, 8):
        c = ws_resumen.cell(row=r_idx, column=c_i)
        c.font = font_bold
        c.fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
        c.border = border_thin

    # Ajustar anchos
    ws_resumen.column_dimensions['A'].width = 8
    ws_resumen.column_dimensions['B'].width = 50
    ws_resumen.column_dimensions['C'].width = 12
    ws_resumen.column_dimensions['D'].width = 8
    ws_resumen.column_dimensions['E'].width = 14
    ws_resumen.column_dimensions['F'].width = 18
    ws_resumen.column_dimensions['G'].width = 20

    # 2. HOJA DETALLE POSTE A POSTE
    ws_detalle = wb.create_sheet(title=f"PROY_{proyecto.numero_emcali}")
    ws_detalle.append(["PROYECTO", proyecto.numero_emcali, "LIQUIDACIÓN POSTE A POSTE"])
    ws_detalle.append([])

    # Encabezados de postes
    encabezado_postes = ["CÓDIGO", "DESCRIPCIÓN", "TOTAL"]
    for ap in apoyos:
        encabezado_postes.append(ap.nodo or f"P{ap.numero_apoyo}")
    ws_detalle.append(encabezado_postes)

    for c_i in range(1, len(encabezado_postes) + 1):
        c = ws_detalle.cell(row=3, column=c_i)
        c.font = font_header
        c.fill = fill_header
        c.alignment = Alignment(horizontal="center", vertical="center")

    r_d = 4
    for item in ItemManoObra.objects.filter(id__in=[i.id for i in totales_por_item.keys()]).order_by("codigo"):
        tot = totales_por_item.get(item, Decimal("0"))
        row_vals = [item.codigo, item.descripcion, float(tot)]
        for ap in apoyos:
            amo = ApoyoManoObra.objects.filter(apoyo=ap, item_mano_obra=item).first()
            row_vals.append(float(amo.cantidad) if amo and amo.cantidad > 0 else 0)
        ws_detalle.append(row_vals)
        for c_i in range(1, len(row_vals) + 1):
            ws_detalle.cell(row=r_d, column=c_i).border = border_thin
        r_d += 1

    ws_detalle.column_dimensions['A'].width = 12
    ws_detalle.column_dimensions['B'].width = 45
    ws_detalle.column_dimensions['C'].width = 12

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"Liquidacion_Ingenieria_Proyecto_{proyecto.numero_emcali}.xlsx"
    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def exportar_liquidacion_macroproyecto_excel(request, macroproyecto_id):
    macro = get_object_or_404(Macroproyecto, id=macroproyecto_id)
    proyectos = macro.proyectos.all().order_by("numero_emcali", "id")

    wb = openpyxl.Workbook()
    ws_macro = wb.active
    ws_macro.title = "CONSOLIDADO_EJECUTIVO"

    # Fuentes y estilos
    font_titulo = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
    font_subtitulo = Font(name="Calibri", size=11, bold=True, color="1E3A8A")
    font_bold = Font(name="Calibri", size=11, bold=True)
    font_normal = Font(name="Calibri", size=11)
    font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")

    fill_navy = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    fill_blue = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")
    fill_gold = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")

    border_thin = Border(
        left=Side(style='thin', color='D1D5DB'),
        right=Side(style='thin', color='D1D5DB'),
        top=Side(style='thin', color='D1D5DB'),
        bottom=Side(style='thin', color='D1D5DB')
    )
    border_double = Border(
        left=Side(style='thin', color='D1D5DB'),
        right=Side(style='thin', color='D1D5DB'),
        top=Side(style='thin', color='D1D5DB'),
        bottom=Side(style='double', color='1E3A8A')
    )

    # 1. BANNER PRINCIPAL
    ws_macro.merge_cells("A1:G1")
    cell_t = ws_macro["A1"]
    cell_t.value = f"COINTECA S.A.S. — LIQUIDACIÓN CONSOLIDADA DE {macro.etiqueta.upper()}"
    cell_t.font = font_titulo
    cell_t.fill = fill_navy
    cell_t.alignment = Alignment(horizontal="center", vertical="center")
    ws_macro.row_dimensions[1].height = 32

    # Metadatos del macroproyecto
    datos_meta = [
        (f"{macro.etiqueta.upper()}:", macro.nombre.upper(), "ESTADO:", macro.estado),
        (f"{macro.etiqueta_codigo_emcali.upper()}:", macro.numero_maniobra_emcali or "N/A", "FECHA EMISIÓN:", timezone.now().strftime("%d/%m/%Y")),
        (f"{macro.etiqueta_codigo_cointeca.upper()}:", macro.numero_maniobra_cointeca or "N/A", f"TOTAL {macro.etiqueta_hijo_plural.upper()}:", f"{proyectos.count()} {macro.etiqueta_hijo_plural.lower()}")
    ]

    r_m = 3
    for fila_m in datos_meta:
        ws_macro.cell(row=r_m, column=1, value=fila_m[0]).font = font_bold
        ws_macro.cell(row=r_m, column=2, value=fila_m[1]).font = font_normal
        ws_macro.cell(row=r_m, column=4, value=fila_m[2]).font = font_bold
        ws_macro.cell(row=r_m, column=5, value=fila_m[3]).font = font_normal
        r_m += 1

    # TABLA 1: RESUMEN POR PROYECTO
    r_m += 1
    ws_macro.cell(row=r_m, column=1, value=f"1. CONSOLIDADO POR {macro.etiqueta_hijo.upper()}").font = font_subtitulo
    r_m += 1

    headers_proy = ["ITEM", f"{macro.etiqueta_hijo.upper()} EMCALI", "TIPO DE RED", "ESTADO", "POSTES", "LUMINARIAS INST.", "TOTAL MANO DE OBRA ($)"]
    ws_macro.append(headers_proy)
    r_header_proy = ws_macro.max_row
    ws_macro.row_dimensions[r_header_proy].height = 24
    for c_i in range(1, 8):
        c = ws_macro.cell(row=r_header_proy, column=c_i)
        c.font = font_header
        c.fill = fill_navy
        c.alignment = Alignment(horizontal="center", vertical="center")

    tot_postes_macro = 0
    tot_lums_macro = 0
    tot_dinero_macro = Decimal("0")
    totales_globales_actividades = defaultdict(lambda: {"item": None, "cantidad": Decimal("0")})

    proyectos_data = []

    for idx, proy in enumerate(proyectos, 1):
        apoyos_proy = Apoyo.objects.filter(proyecto=proy).order_by("numero_apoyo", "id")
        num_postes = apoyos_proy.count()
        tot_postes_macro += num_postes

        num_lums = ApoyoLuminaria.objects.filter(apoyo__proyecto=proy).count()
        tot_lums_macro += num_lums

        apoyos_ids = apoyos_proy.values_list("id", flat=True)
        amos = ApoyoManoObra.objects.filter(apoyo_id__in=apoyos_ids).select_related("item_mano_obra")
        dinero_proy = Decimal("0")
        totales_item_proy = defaultdict(Decimal)

        for amo in amos:
            totales_item_proy[amo.item_mano_obra] += amo.cantidad
            totales_globales_actividades[amo.item_mano_obra.id]["item"] = amo.item_mano_obra
            totales_globales_actividades[amo.item_mano_obra.id]["cantidad"] += amo.cantidad

        for it, cant in totales_item_proy.items():
            dinero_proy += cant * it.valor_unitario

        tot_dinero_macro += dinero_proy

        proyectos_data.append({
            "proyecto": proy,
            "apoyos": apoyos_proy,
            "totales_item": totales_item_proy,
            "dinero_total": dinero_proy
        })

        ws_macro.append([
            idx,
            proy.numero_emcali,
            proy.get_tipo_display() if hasattr(proy, 'get_tipo_display') else proy.tipo,
            proy.estado,
            num_postes,
            num_lums,
            float(dinero_proy)
        ])
        r_actual = ws_macro.max_row
        for c_i in range(1, 8):
            cell = ws_macro.cell(row=r_actual, column=c_i)
            cell.border = border_thin
            if c_i in [1, 5, 6]:
                cell.alignment = Alignment(horizontal="center")
            elif c_i == 7:
                cell.alignment = Alignment(horizontal="right")
                cell.number_format = '"$"#,##0'

    # Fila de totales de proyectos
    ws_macro.append(["", f"TOTAL {macro.etiqueta.upper()}", "", "", tot_postes_macro, tot_lums_macro, float(tot_dinero_macro)])
    r_tot_p = ws_macro.max_row
    ws_macro.row_dimensions[r_tot_p].height = 22
    for c_i in range(1, 8):
        cell = ws_macro.cell(row=r_tot_p, column=c_i)
        cell.font = font_bold
        cell.fill = fill_gold
        cell.border = border_double
        if c_i in [5, 6]:
            cell.alignment = Alignment(horizontal="center")
        elif c_i == 7:
            cell.alignment = Alignment(horizontal="right")
            cell.number_format = '"$"#,##0'

    # TABLA 2: CONSOLIDADO MAESTRO DE ACTIVIDADES (TODO EL MACROPROYECTO / CIRCUITO)
    ws_macro.append([])
    ws_macro.append([])
    ws_macro.cell(row=ws_macro.max_row, column=1, value=f"2. CONSOLIDADO GLOBAL DE ACTIVIDADES DE MANO DE OBRA ({macro.etiqueta.upper()} COMPLETO)").font = font_subtitulo

    headers_mo = ["ITEM", "CÓDIGO", "DESCRIPCIÓN DE LA ACTIVIDAD / SERVICIO", "UND", "CANTIDAD TOTAL", "VALOR UNITARIO ($)", "VALOR TOTAL ($)"]
    ws_macro.append(headers_mo)
    r_header_mo = ws_macro.max_row
    ws_macro.row_dimensions[r_header_mo].height = 24
    for c_i in range(1, 8):
        c = ws_macro.cell(row=r_header_mo, column=c_i)
        c.font = font_header
        c.fill = fill_blue
        c.alignment = Alignment(horizontal="center", vertical="center")

    actividades_ordenadas = sorted(
        [v for v in totales_globales_actividades.values() if v["cantidad"] > 0],
        key=lambda x: x["item"].codigo
    )

    tot_acum_mo = Decimal("0")
    for a_idx, act in enumerate(actividades_ordenadas, 1):
        item_obj = act["item"]
        cant_tot = act["cantidad"]
        subt = cant_tot * item_obj.valor_unitario
        tot_acum_mo += subt

        ws_macro.append([
            a_idx,
            item_obj.codigo,
            item_obj.descripcion,
            item_obj.unidad,
            float(cant_tot),
            float(item_obj.valor_unitario),
            float(subt)
        ])
        r_actual_mo = ws_macro.max_row
        for c_i in range(1, 8):
            cell = ws_macro.cell(row=r_actual_mo, column=c_i)
            cell.border = border_thin
            if c_i in [1, 2, 4]:
                cell.alignment = Alignment(horizontal="center")
            elif c_i == 5:
                cell.alignment = Alignment(horizontal="right")
                cell.number_format = '#,##0.00'
            elif c_i in [6, 7]:
                cell.alignment = Alignment(horizontal="right")
                cell.number_format = '"$"#,##0'

    # Fila total de actividades
    ws_macro.append(["", "TOTAL MANO DE OBRA CONSOLIDADA", "", "", "", "", float(tot_acum_mo)])
    r_tot_mo = ws_macro.max_row
    ws_macro.row_dimensions[r_tot_mo].height = 22
    for c_i in range(1, 8):
        cell = ws_macro.cell(row=r_tot_mo, column=c_i)
        cell.font = font_bold
        cell.fill = fill_gold
        cell.border = border_double
        if c_i == 7:
            cell.alignment = Alignment(horizontal="right")
            cell.number_format = '"$"#,##0'

    # Ajustar anchos en hoja de resumen
    ws_macro.column_dimensions['A'].width = 8
    ws_macro.column_dimensions['B'].width = 24
    ws_macro.column_dimensions['C'].width = 52
    ws_macro.column_dimensions['D'].width = 16
    ws_macro.column_dimensions['E'].width = 18
    ws_macro.column_dimensions['F'].width = 20
    ws_macro.column_dimensions['G'].width = 24

    # PESTAÑAS INDIVIDUALES POR CADA PROYECTO (Desglose poste a poste)
    for pdata in proyectos_data:
        proy = pdata["proyecto"]
        apoyos_proy = pdata["apoyos"]
        totales_item_proy = pdata["totales_item"]
        safe_title = f"PROY_{proy.numero_emcali}"[:31]
        ws_det = wb.create_sheet(title=safe_title)

        ws_det.append(["PROYECTO:", proy.numero_emcali, "TIPO:", proy.get_tipo_display() if hasattr(proy, 'get_tipo_display') else proy.tipo, "MACROPROYECTO:", macro.nombre])
        ws_det.append([])

        encabezado_postes = ["CÓDIGO", "DESCRIPCIÓN ACTIVIDAD", "UND", "CANT. TOTAL", "VR. UNITARIO ($)", "SUBTOTAL ($)"]
        for ap in apoyos_proy:
            encabezado_postes.append(ap.nodo or f"P{ap.numero_apoyo}")

        ws_det.append(encabezado_postes)
        r_head = ws_det.max_row
        ws_det.row_dimensions[r_head].height = 24
        for c_i in range(1, len(encabezado_postes) + 1):
            c = ws_det.cell(row=r_head, column=c_i)
            c.font = font_header
            c.fill = fill_navy
            c.alignment = Alignment(horizontal="center", vertical="center")

        items_proy_ordenados = sorted(
            [it for it in totales_item_proy.keys() if totales_item_proy[it] > 0],
            key=lambda x: x.codigo
        )

        for item in items_proy_ordenados:
            tot = totales_item_proy.get(item, Decimal("0"))
            v_unit = item.valor_unitario
            sub_val = tot * v_unit
            row_vals = [item.codigo, item.descripcion, item.unidad, float(tot), float(v_unit), float(sub_val)]
            for ap in apoyos_proy:
                amo = ApoyoManoObra.objects.filter(apoyo=ap, item_mano_obra=item).first()
                row_vals.append(float(amo.cantidad) if amo and amo.cantidad > 0 else 0)
            ws_det.append(row_vals)
            r_det = ws_det.max_row
            for c_i in range(1, len(row_vals) + 1):
                cell = ws_det.cell(row=r_det, column=c_i)
                cell.border = border_thin
                if c_i in [1, 3]:
                    cell.alignment = Alignment(horizontal="center")
                elif c_i == 4:
                    cell.alignment = Alignment(horizontal="right")
                    cell.number_format = '#,##0.00'
                elif c_i in [5, 6]:
                    cell.alignment = Alignment(horizontal="right")
                    cell.number_format = '"$"#,##0'
                elif c_i > 6:
                    cell.alignment = Alignment(horizontal="center")

        # Fila total del proyecto
        fila_tot_proy = ["", f"TOTAL {proy.etiqueta.upper()}", "", "", "", float(pdata["dinero_total"])]
        for _ in apoyos_proy:
            fila_tot_proy.append("")
        ws_det.append(fila_tot_proy)
        r_f_tot = ws_det.max_row
        ws_det.row_dimensions[r_f_tot].height = 22
        for c_i in range(1, len(fila_tot_proy) + 1):
            cell = ws_det.cell(row=r_f_tot, column=c_i)
            cell.font = font_bold
            cell.fill = fill_gold
            cell.border = border_double
            if c_i == 6:
                cell.alignment = Alignment(horizontal="right")
                cell.number_format = '"$"#,##0'

        ws_det.column_dimensions['A'].width = 12
        ws_det.column_dimensions['B'].width = 45
        ws_det.column_dimensions['C'].width = 8
        ws_det.column_dimensions['D'].width = 14
        ws_det.column_dimensions['E'].width = 16
        ws_det.column_dimensions['F'].width = 18

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    nombre_archivo = f"Liquidacion_{macro.etiqueta}_{macro.nombre.replace(' ', '_')}_{timezone.now().strftime('%Y%m%d')}.xlsx"
    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{nombre_archivo}"'
    return response
