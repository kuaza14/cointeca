from collections import defaultdict
from core.helpers.ingenieria_calculo import calcular_mano_obra_proyecto_completo, calcular_mano_obra_para_apoyo, actualizar_presupuesto_proyecto
import io
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
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
    ItemManoObra,
    ApoyoManoObra,
    Presupuesto,
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

    return render(
        request,
        "ingenieria/macroproyectos/lista.html",
        {
            "macroproyectos": resumen_macros,
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

        macro = Macroproyecto.objects.create(
            nombre=nombre,
            numero_maniobra_emcali=numero_maniobra_emcali,
            numero_maniobra_cointeca=numero_maniobra_cointeca,
            descripcion=descripcion,
            estado=estado if estado in Macroproyecto.Estados.values else Macroproyecto.Estados.PLANEACION
        )
        messages.success(request, f"Macroproyecto '{macro.nombre}' creado exitosamente.")
        return redirect("lista_macroproyectos")
    return redirect("lista_macroproyectos")

@login_required
def editar_macroproyecto(request, id):
    macro = get_object_or_404(Macroproyecto, id=id)

    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        numero_maniobra_emcali = request.POST.get("numero_maniobra_emcali", "").strip()
        numero_maniobra_cointeca = request.POST.get("numero_maniobra_cointeca", "").strip()
        descripcion = request.POST.get("descripcion", "").strip()
        estado = request.POST.get("estado", macro.estado).strip()

        if not nombre:
            messages.error(request, "El nombre del macroproyecto es obligatorio.")
            return redirect("lista_macroproyectos")

        if Macroproyecto.objects.filter(nombre__iexact=nombre).exclude(id=macro.id).exists():
            messages.error(request, f"Ya existe otro macroproyecto con el nombre '{nombre}'.")
            return redirect("lista_macroproyectos")

        macro.nombre = nombre
        macro.numero_maniobra_emcali = numero_maniobra_emcali
        macro.numero_maniobra_cointeca = numero_maniobra_cointeca
        macro.descripcion = descripcion
        if estado in Macroproyecto.Estados.values:
            macro.estado = estado
        macro.save()

        messages.success(request, f"Macroproyecto '{macro.nombre}' actualizado correctamente.")
        return redirect("lista_macroproyectos")
    return redirect("lista_macroproyectos")

@login_required
@transaction.atomic
def eliminar_macroproyecto(request, id):
    macro = Macroproyecto.objects.filter(id=id).first()
    if not macro:
        messages.warning(request, "El macroproyecto que intentas eliminar ya no existe.")
        return redirect("lista_macroproyectos")

    if request.method == "POST":
        nombre = macro.nombre
        macro.delete()
        messages.success(request, f"Macroproyecto '{nombre}' y todos sus proyectos asociados han sido eliminados.")
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

    if query:
        proyectos = proyectos.filter(
            Q(numero_emcali__icontains=query) |
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
            messages.error(request, "El número de proyecto y el tipo de red son obligatorios.")
            return _volver()

        if Proyecto.objects.filter(numero_emcali__iexact=numero_emcali).exists():
            messages.error(request, f"Ya existe un proyecto registrado con el número '{numero_emcali}'.")
            return _volver()

        proyecto = Proyecto.objects.create(
            macroproyecto=macroproyecto,
            numero_emcali=numero_emcali,
            tipo=tipo,
            estado=estado if estado in Proyecto.Estados.values else Proyecto.Estados.PLANEACION
        )
        messages.success(request, f"Proyecto '{proyecto.numero_emcali}' creado exitosamente.")
        return _volver()

    if macroproyecto_id:
        return redirect("proyectos_por_macroproyecto", macroproyecto_id=macroproyecto_id)
    return redirect("lista_proyectos")

@login_required
def editar_proyecto(request, id):
    proyecto = get_object_or_404(Proyecto, id=id)

    if request.method == "POST":
        numero_emcali = request.POST.get("numero_emcali", "").strip()
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
            messages.error(request, "El número de proyecto y el tipo de red son obligatorios.")
            return _volver()

        if Proyecto.objects.filter(numero_emcali__iexact=numero_emcali).exclude(id=proyecto.id).exists():
            messages.error(request, f"Ya existe otro proyecto registrado con el número '{numero_emcali}'.")
            return _volver()

        proyecto.numero_emcali = numero_emcali
        proyecto.tipo = tipo
        if estado in Proyecto.Estados.values:
            proyecto.estado = estado
        proyecto.save()

        messages.success(request, f"Proyecto '{proyecto.numero_emcali}' actualizado correctamente.")
        return _volver()

    if proyecto.macroproyecto:
        return redirect("proyectos_por_macroproyecto", macroproyecto_id=proyecto.macroproyecto.id)
    return redirect("lista_proyectos")

@login_required
@transaction.atomic
def eliminar_proyecto(request, id):
    proyecto = Proyecto.objects.filter(id=id).first()
    if not proyecto:
        messages.warning(request, "El proyecto que intentas eliminar ya no existe.")
        return redirect("lista_proyectos")

    macro_id = proyecto.macroproyecto_id
    if request.method == "POST":
        nombre = proyecto.numero_emcali
        proyecto.delete()
        messages.success(request, f"Proyecto '{nombre}' y todos sus apoyos/materiales han sido eliminados correctamente.")
    
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

    # 3. Cargar TODA la Mano de Obra del proyecto en 1 sola consulta (sin N+1)
    apoyos_mo = list(
        ApoyoManoObra.objects.filter(
            apoyo__proyecto=proyecto
        ).select_related("item_mano_obra")
    )

    mo_dict = {}
    mo_cant_map = {}
    mo_origen_map = {}
    mo_id_map = {}
    apoyo_mo_map = defaultdict(list)

    for amo in apoyos_mo:
        mo_cant_map[(amo.apoyo_id, amo.item_mano_obra_id)] = amo.cantidad
        mo_origen_map[(amo.apoyo_id, amo.item_mano_obra_id)] = amo.origen
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
            amo_id = mo_id_map.get((ap.id, item.id))
            celdas_mo.append({
                "item": item,
                "cantidad": cant_mo,
                "origen": orig,
                "amo_id": amo_id,
            })
            mo_totales_columna[item.id] += cant_mo

        mo_filas_matriz.append({
            "apoyo": ap,
            "celdas": celdas_mo,
            "manos_obra_list": apoyo_mo_map.get(ap.id, []),
            "materiales_asociados": apoyo_materiales_map.get(ap.id, []),
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
            "materiales_catalogo": materiales_catalogo,
            "empleados": empleados,
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

        # Guardar materiales asignados (múltiples)
        materiales_ids = request.POST.getlist("material_id[]")
        cantidades_inst = request.POST.getlist("cantidad_instalada[]") or request.POST.getlist("cantidad[]")
        cantidades_ret = request.POST.getlist("cantidad_retirada[]")

        materiales_creados = 0
        for i, mat_id in enumerate(materiales_ids):
            if not mat_id:
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
                    if inventario.cantidad >= c_inst:
                        inventario.cantidad -= c_inst
                    else:
                        inventario.cantidad = Decimal("0")

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
                    if diferencia > 0:
                        if inventario.cantidad >= diferencia:
                            inventario.cantidad -= diferencia
                        else:
                            inventario.cantidad = Decimal("0")
                    elif diferencia < 0:
                        inventario.cantidad += abs(diferencia)

                    diferencia_ret = c_ret - am.cantidad_retirada
                    if diferencia_ret != 0:
                        inventario.cantidad += diferencia_ret
                        inventario.cantidad = max(Decimal("0"), inventario.cantidad)

                    inventario.save()

                    am.cantidad_requerida = max(Decimal("0"), c_inst)
                    am.cantidad_retirada = max(Decimal("0"), c_ret)
                    am.save()
                else:
                    if c_inst > 0:
                        if inventario.cantidad >= c_inst:
                            inventario.cantidad -= c_inst
                        else:
                            inventario.cantidad = Decimal("0")

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

        # Eliminar materiales que se hayan removido
        for mat_id_antiguo, am in materiales_actuales.items():
            if mat_id_antiguo not in materiales_nuevos_procesados:
                inv_del, _ = Inventario.objects.get_or_create(material_id=mat_id_antiguo)
                if am.cantidad_requerida > 0:
                    inv_del.cantidad += am.cantidad_requerida
                if am.cantidad_retirada > 0:
                    inv_del.cantidad = max(Decimal("0"), inv_del.cantidad - am.cantidad_retirada)
                inv_del.save()
                am.delete()

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

        warning_msg = None
        # Descontar del inventario general de bodega
        if stock_previo <= 0:
            warning_msg = f"⚠️ Advertencia: '{material.descripcion}' no tiene existencias en bodega central (Stock: 0 {unidad_str}). Se despacharon {cant} {unidad_str} al poste como requerimiento pendiente de compra."
            if not is_ajax:
                messages.warning(request, warning_msg)
        elif stock_previo < cant:
            inventario.cantidad = Decimal("0")
            inventario.save()
            warning_msg = f"⚠️ Advertencia: Stock insuficiente en bodega para '{material.descripcion}'. Había {stock_previo} {unidad_str} y se solicitaron {cant} {unidad_str}. Se agotó el stock disponible en bodega."
            if not is_ajax:
                messages.warning(request, warning_msg)
        else:
            inventario.cantidad -= cant
            inventario.save()
            if not is_ajax:
                messages.success(
                    request,
                    f"Se despacharon exitosamente {cant} {unidad_str} de '{material.descripcion}' desde Bodega Central al poste (Stock restante en bodega: {inventario.cantidad} {unidad_str})."
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
                "message": f"Se despacharon {cant} {unidad_str} de '{material.descripcion}' al poste.",
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
@transaction.atomic
def detalle_apoyo(request, apoyo_id):
    apoyo = Apoyo.objects.filter(id=apoyo_id).first()
    if not apoyo:
        messages.warning(request, "El poste o apoyo seleccionado no existe o fue removido previamente.")
        return redirect("lista_proyectos")

    materiales_asociados = ApoyoMaterial.objects.filter(
        apoyo=apoyo
    ).select_related("material", "material__inventario").order_by("material__descripcion")

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
                        stock_previo = inventario.cantidad
                        unidad_str = material.unidad or "UN"

                        # Descontar del inventario general de bodega
                        if stock_previo <= 0:
                            messages.warning(
                                request,
                                f"⚠️ Advertencia: '{material.descripcion}' no tiene existencias en bodega central (Stock: 0 {unidad_str}). Se despacharon/asignaron {cant} {unidad_str} al poste como requerimiento pendiente de compra/entrada."
                            )
                        elif stock_previo < cant:
                            inventario.cantidad = Decimal("0")
                            inventario.save()
                            messages.warning(
                                request,
                                f"⚠️ Advertencia: Stock insuficiente en bodega para '{material.descripcion}'. Había {stock_previo} {unidad_str} y se solicitaron {cant} {unidad_str}. Se agotó el stock disponible y el resto queda pendiente."
                            )
                        else:
                            inventario.cantidad -= cant
                            inventario.save()
                            messages.success(
                                request,
                                f"Se despacharon {cant} {unidad_str} de '{material.descripcion}' al poste. Stock disponible restante: {inventario.cantidad} {unidad_str}."
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
                        actualizar_presupuesto_proyecto(apoyo.proyecto)

                except (ValueError, TypeError):
                    pass

            return redirect("detalle_apoyo", apoyo_id=apoyo.id)

        # 2. EDITAR MATERIAL ASIGNADO (INSTALADO Y RETIRADO)
        if accion == "editar_material":
            item_id = request.POST.get("item_id")
            cantidad_inst_str = request.POST.get("cantidad_instalada", "0")
            cantidad_ret_str = request.POST.get("cantidad_retirada", "0")

            try:
                cant_inst = Decimal(cantidad_inst_str.strip()) if cantidad_inst_str else Decimal("0")
                cant_ret = Decimal(cantidad_ret_str.strip()) if cantidad_ret_str else Decimal("0")

                if item_id:
                    apoyo_mat = ApoyoMaterial.objects.filter(
                        id=item_id,
                        apoyo=apoyo
                    ).first()

                    if apoyo_mat:
                        diferencia = cant_inst - apoyo_mat.cantidad_requerida
                        unidad_str = apoyo_mat.material.unidad or "UN"
                        inventario, _ = Inventario.objects.get_or_create(material=apoyo_mat.material)

                        if diferencia > 0:
                            if inventario.cantidad <= 0:
                                messages.warning(
                                    request,
                                    f"⚠️ Advertencia: '{apoyo_mat.material.descripcion}' no tiene existencias en bodega (Stock: 0 {unidad_str}). Se aumentó la cantidad instalada en el poste a {cant_inst} {unidad_str} como proyección técnica."
                                )
                            elif inventario.cantidad < diferencia:
                                messages.warning(
                                    request,
                                    f"⚠️ Advertencia: Stock insuficiente en bodega para '{apoyo_mat.material.descripcion}'. Se consumió el remanente de {inventario.cantidad} {unidad_str}."
                                )
                                inventario.cantidad = Decimal("0")
                            else:
                                inventario.cantidad -= diferencia
                        elif diferencia < 0:
                            inventario.cantidad += abs(diferencia)

                        diferencia_ret = cant_ret - apoyo_mat.cantidad_retirada
                        if diferencia_ret != 0:
                            inventario.cantidad += diferencia_ret
                            inventario.cantidad = max(Decimal("0"), inventario.cantidad)

                        inventario.save()
                        messages.success(request, f"Cantidades actualizadas para '{apoyo_mat.material.descripcion}'.")

                        apoyo_mat.cantidad_requerida = max(Decimal("0"), cant_inst)
                        apoyo_mat.cantidad_retirada = max(Decimal("0"), cant_ret)
                        apoyo_mat.save()

                        calcular_mano_obra_para_apoyo(apoyo)
                        actualizar_presupuesto_proyecto(apoyo.proyecto)

            except (ValueError, TypeError, ArithmeticError):
                pass

            return redirect("detalle_apoyo", apoyo_id=apoyo.id)

        # 3. ELIMINAR MATERIAL DEL APOYO (DEVUELVE LO INSTALADO A BODEGA)
        if accion == "eliminar_material":
            item_id = request.POST.get("item_id")

            if item_id:
                apoyo_mat = ApoyoMaterial.objects.filter(
                    id=item_id,
                    apoyo=apoyo
                ).first()

                if apoyo_mat:
                    nombre_mat = apoyo_mat.material.descripcion
                    inv_del, _ = Inventario.objects.get_or_create(material=apoyo_mat.material)
                    if apoyo_mat.cantidad_requerida > 0:
                        inv_del.cantidad += apoyo_mat.cantidad_requerida
                    if apoyo_mat.cantidad_retirada > 0:
                        inv_del.cantidad = max(Decimal("0"), inv_del.cantidad - apoyo_mat.cantidad_retirada)
                    inv_del.save()

                    apoyo_mat.delete()
                    calcular_mano_obra_para_apoyo(apoyo)
                    actualizar_presupuesto_proyecto(apoyo.proyecto)
                    messages.success(request, f"Material '{nombre_mat}' eliminado de este apoyo.")

            return redirect("detalle_apoyo", apoyo_id=apoyo.id)

        # 4. GUARDAR DATOS PRINCIPALES DEL APOYO
        apoyo.nodo = request.POST.get("nodo", "").strip()

        numero_apoyo = request.POST.get("numero_apoyo")
        apoyo.numero_apoyo = (
            int(numero_apoyo)
            if numero_apoyo and numero_apoyo.isdigit()
            else None
        )

        fecha_val = request.POST.get("fecha")
        apoyo.fecha = fecha_val.strip() if fecha_val and fecha_val.strip() else None

        apoyo.tipo_instalacion = request.POST.get("tipo_instalacion", "").strip()
        apoyo.direccion = request.POST.get("direccion", "").strip()
        apoyo.tipo_estructura = request.POST.get("tipo_estructura", "").strip()

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

        materiales_sin_stock = []
        cambios_realizados = False

        # 5. ACTUALIZAR / EDITAR MATERIALES EXISTENTES EN EL APOYO
        asociados_ids = request.POST.getlist("asociado_id[]")
        asociados_mat_ids = request.POST.getlist("asociado_material_id[]")
        asociados_c_inst = request.POST.getlist("asociado_cant_instalada[]")
        asociados_c_ret = request.POST.getlist("asociado_cant_retirada[]")

        for i, a_id in enumerate(asociados_ids):
            if not a_id:
                continue
            apoyo_mat = ApoyoMaterial.objects.filter(id=a_id, apoyo=apoyo).first()
            if not apoyo_mat:
                continue

            try:
                c_inst_raw = asociados_c_inst[i] if i < len(asociados_c_inst) else None
                c_ret_raw = asociados_c_ret[i] if i < len(asociados_c_ret) else None

                c_inst_str = str(c_inst_raw).strip().replace(',', '.') if c_inst_raw is not None else ""
                c_ret_str = str(c_ret_raw).strip().replace(',', '.') if c_ret_raw is not None else ""

                if c_inst_str != "":
                    c_inst = Decimal(c_inst_str)
                else:
                    c_inst = apoyo_mat.cantidad_requerida

                if c_ret_str != "":
                    c_ret = Decimal(c_ret_str)
                else:
                    c_ret = apoyo_mat.cantidad_retirada

                # Cambio de material si el usuario seleccionó uno diferente
                mat_id_nuevo = asociados_mat_ids[i] if i < len(asociados_mat_ids) and asociados_mat_ids[i] else str(apoyo_mat.material_id)

                if str(mat_id_nuevo) != str(apoyo_mat.material_id):
                    # Devolver stock anterior
                    inv_ant, _ = Inventario.objects.get_or_create(material=apoyo_mat.material)
                    if apoyo_mat.cantidad_requerida > 0:
                        inv_ant.cantidad += apoyo_mat.cantidad_requerida
                    if apoyo_mat.cantidad_retirada > 0:
                        inv_ant.cantidad = max(Decimal("0"), inv_ant.cantidad - apoyo_mat.cantidad_retirada)
                    inv_ant.save()

                    nuevo_mat = Material.objects.filter(id=mat_id_nuevo).first()
                    if nuevo_mat:
                        apoyo_mat.material = nuevo_mat
                        apoyo_mat.cantidad_requerida = Decimal("0")
                        apoyo_mat.cantidad_retirada = Decimal("0")

                inventario, _ = Inventario.objects.get_or_create(material=apoyo_mat.material)
                mat_obj = inventario.material
                unidad_str = mat_obj.unidad or "UN"

                diferencia = c_inst - apoyo_mat.cantidad_requerida
                if diferencia > 0:
                    if inventario.cantidad <= 0:
                        materiales_sin_stock.append(f"{mat_obj.descripcion} (Stock: 0, Solicitado: {c_inst} {unidad_str})")
                    elif inventario.cantidad < diferencia:
                        materiales_sin_stock.append(f"{mat_obj.descripcion} (Stock: {inventario.cantidad}, Solicitado: {c_inst} {unidad_str})")
                        inventario.cantidad = Decimal("0")
                        inventario.save()
                    else:
                        inventario.cantidad -= diferencia
                        inventario.save()
                elif diferencia < 0:
                    inventario.cantidad += abs(diferencia)
                    inventario.save()

                diferencia_ret = c_ret - apoyo_mat.cantidad_retirada
                if diferencia_ret != 0:
                    inventario.cantidad += diferencia_ret
                    inventario.cantidad = max(Decimal("0"), inventario.cantidad)
                    inventario.save()

                apoyo_mat.cantidad_requerida = max(Decimal("0"), c_inst)
                apoyo_mat.cantidad_retirada = max(Decimal("0"), c_ret)
                apoyo_mat.save()
                cambios_realizados = True

            except (ValueError, TypeError, ArithmeticError):
                continue

        # 6. GUARDAR NUEVOS MATERIALES ASIGNADOS AL APOYO
        materiales_ids = request.POST.getlist("material_id[]")
        cantidades_inst = request.POST.getlist("cantidad_instalada[]") or request.POST.getlist("cantidad[]")
        cantidades_ret = request.POST.getlist("cantidad_retirada[]")

        for i, mat_id in enumerate(materiales_ids):
            if not mat_id:
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
                mat_obj = inventario.material
                unidad_str = mat_obj.unidad or "UN"

                apoyo_mat = ApoyoMaterial.objects.filter(
                    apoyo=apoyo,
                    material_id=mat_id
                ).first()

                if apoyo_mat:
                    diferencia = c_inst
                    if diferencia > 0:
                        if inventario.cantidad <= 0:
                            materiales_sin_stock.append(f"{mat_obj.descripcion} (Stock: 0, Solicitado: {c_inst} {unidad_str})")
                        elif inventario.cantidad < diferencia:
                            materiales_sin_stock.append(f"{mat_obj.descripcion} (Stock: {inventario.cantidad}, Solicitado: {c_inst} {unidad_str})")
                            inventario.cantidad = Decimal("0")
                        else:
                            inventario.cantidad -= diferencia

                    if c_ret > 0:
                        inventario.cantidad += c_ret

                    inventario.save()

                    apoyo_mat.cantidad_requerida += c_inst
                    apoyo_mat.cantidad_retirada += c_ret
                    apoyo_mat.save()
                else:
                    if c_inst > 0:
                        if inventario.cantidad <= 0:
                            materiales_sin_stock.append(f"{mat_obj.descripcion} (Stock: 0, Asignado: {c_inst} {unidad_str})")
                        elif inventario.cantidad < c_inst:
                            materiales_sin_stock.append(f"{mat_obj.descripcion} (Stock: {inventario.cantidad}, Asignado: {c_inst} {unidad_str})")
                            inventario.cantidad = Decimal("0")
                        else:
                            inventario.cantidad -= c_inst

                    if c_ret > 0:
                        inventario.cantidad += c_ret

                    inventario.save()

                    ApoyoMaterial.objects.create(
                        apoyo=apoyo,
                        material_id=mat_id,
                        cantidad_requerida=c_inst,
                        cantidad_retirada=c_ret
                    )

                cambios_realizados = True

            except (ValueError, TypeError, ArithmeticError):
                continue

        if materiales_sin_stock:
            lista_str = "; ".join(materiales_sin_stock)
            messages.warning(
                request,
                f"⚠️ Aviso de Stock en Bodega: Los siguientes materiales no cuentan con suficiente stock disponible: [{lista_str}]. Han quedado guardados en este poste como proyección técnica de la obra y se conciliarán en la matriz de balance de logística."
            )
        else:
            messages.success(request, "Los datos y materiales del apoyo se han guardado exitosamente.")

        # Recalcular Mano de Obra y Presupuesto
        calcular_mano_obra_para_apoyo(apoyo)
        actualizar_presupuesto_proyecto(apoyo.proyecto)

        # DECIDIR A DÓNDE VOLVER
        if "guardar_y_volver" in request.POST:
            return redirect("detalle_proyecto", id=apoyo.proyecto.id)

        return redirect("detalle_apoyo", apoyo_id=apoyo.id)

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

                if cant_inst > 0:
                    if inventario.cantidad < cant_inst:
                        messages.warning(
                            request,
                            f"⚠️ Stock insuficiente en bodega para '{material.descripcion}' (Stock disponible: {inventario.cantidad}). Se asignaron {cant_inst} como requerimiento proyectado."
                        )
                        inventario.cantidad = Decimal("0")
                    else:
                        inventario.cantidad -= cant_inst

                if cant_ret > 0:
                    inventario.cantidad += cant_ret

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

            diferencia = cant_inst - apoyo_mat.cantidad_requerida
            if diferencia > 0:
                if inventario.cantidad < diferencia:
                    inventario.cantidad = Decimal("0")
                else:
                    inventario.cantidad -= diferencia
            elif diferencia < 0:
                inventario.cantidad += abs(diferencia)

            diferencia_ret = cant_ret - apoyo_mat.cantidad_retirada
            if diferencia_ret != 0:
                inventario.cantidad += diferencia_ret
                inventario.cantidad = max(Decimal("0"), inventario.cantidad)

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
            if apoyo_mat.cantidad_requerida > 0:
                inv_del.cantidad += apoyo_mat.cantidad_requerida
            if apoyo_mat.cantidad_retirada > 0:
                inv_del.cantidad = max(Decimal("0"), inv_del.cantidad - apoyo_mat.cantidad_retirada)
            inv_del.save()

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
    Permite agregar o editar una actividad de mano de obra específica en un apoyo.
    """
    apoyo = Apoyo.objects.filter(id=apoyo_id).first()
    if not apoyo:
        messages.warning(request, "El poste o apoyo seleccionado ya no existe.")
        return redirect("lista_proyectos")

    if request.method == "POST":
        item_id = request.POST.get("item_mano_obra_id")
        cantidad_str = request.POST.get("cantidad", "0").strip().replace(',', '.')
        observacion = request.POST.get("observacion", "").strip()

        if item_id:
            try:
                cantidad = Decimal(cantidad_str) if cantidad_str else Decimal("0")
                item = ItemManoObra.objects.filter(id=item_id).first()
                if not item:
                    messages.error(request, "La actividad de mano de obra seleccionada no es válida.")
                    return redirect(f"/ingenieria/proyectos/{apoyo.proyecto.id}/?tab=mano_obra" if apoyo.proyecto else "lista_proyectos")

                if cantidad > 0:
                    amo, _ = ApoyoManoObra.objects.get_or_create(
                        apoyo=apoyo,
                        item_mano_obra=item,
                        defaults={"cantidad": cantidad, "origen": ApoyoManoObra.Origen.MANUAL, "observacion": observacion}
                    )
                    amo.cantidad = cantidad
                    amo.origen = ApoyoManoObra.Origen.MANUAL
                    amo.observacion = observacion
                    amo.save()
                    messages.success(request, f"Actividad '{item.descripcion}' asignada al apoyo {apoyo.nodo or apoyo.numero_apoyo}.")
                else:
                    ApoyoManoObra.objects.filter(apoyo=apoyo, item_mano_obra=item).delete()
                    messages.info(request, f"Actividad '{item.descripcion}' removida del apoyo.")

                if apoyo.proyecto:
                    actualizar_presupuesto_proyecto(apoyo.proyecto)
            except Exception as e:
                messages.error(request, f"Error al guardar actividad: {e}")

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

    ws_resumen.append(["", "MICROPROYECTO", proyecto.numero_emcali, "", "FECHA", timezone.now().strftime("%d/%m/%Y")])
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
