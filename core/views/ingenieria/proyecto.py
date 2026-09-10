import io
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
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
        descripcion = request.POST.get("descripcion", "").strip()
        estado = request.POST.get("estado", macro.estado).strip()

        if not nombre:
            messages.error(request, "El nombre del macroproyecto es obligatorio.")
            return redirect("lista_macroproyectos")

        if Macroproyecto.objects.filter(nombre__iexact=nombre).exclude(id=macro.id).exists():
            messages.error(request, f"Ya existe otro macroproyecto con el nombre '{nombre}'.")
            return redirect("lista_macroproyectos")

        macro.nombre = nombre
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
    macro = get_object_or_404(Macroproyecto, id=id)
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
    proyecto = get_object_or_404(Proyecto, id=id)
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
    materiales_columnas = list(Material.objects.filter(id__in=materiales_ids).order_by("item", "descripcion"))

    cantidades_inst_map = {}
    cantidades_ret_map = {}
    for am in apoyo_materiales:
        cantidades_inst_map[(am.apoyo_id, am.material_id)] = am.cantidad_requerida
        cantidades_ret_map[(am.apoyo_id, am.material_id)] = am.cantidad_retirada

    # 3. Construir filas de la matriz estilo Excel (Filas = Apoyos/Nodos, Columnas = Materiales)
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
        })

    # 4. Fila de Totales Generales
    fila_totales = []
    for mat in materiales_columnas:
        fila_totales.append({
            "material": mat,
            "total": totales_inst_columna.get(mat.id, Decimal("0")),
            "total_retirado": totales_ret_columna.get(mat.id, Decimal("0")),
        })

    # 5. Resumen de Materiales Retirados en el Proyecto
    tabla_resumen_retiros = []
    for mat in materiales_columnas:
        tot_ret = totales_ret_columna.get(mat.id, Decimal("0"))
        if tot_ret > 0:
            tabla_resumen_retiros.append({
                "material": mat,
                "cantidad_retirada": tot_ret,
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
            "tabla_resumen_retiros": tabla_resumen_retiros,
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
                        unidad_str = material.unidad or "U"

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
                        unidad_str = apoyo_mat.material.unidad or "U"
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
                                inventario.save()
                            else:
                                inventario.cantidad -= diferencia
                                inventario.save()
                                messages.success(request, f"Cantidades actualizadas para '{apoyo_mat.material.descripcion}'.")
                        elif diferencia < 0:
                            inventario.cantidad += abs(diferencia)
                            inventario.save()
                            messages.success(request, f"Cantidades actualizadas para '{apoyo_mat.material.descripcion}' (se devolvieron {abs(diferencia)} {unidad_str} a bodega).")
                        else:
                            messages.success(request, f"Cantidades actualizadas para '{apoyo_mat.material.descripcion}'.")

                        apoyo_mat.cantidad_requerida = max(Decimal("0"), cant_inst)
                        apoyo_mat.cantidad_retirada = max(Decimal("0"), cant_ret)
                        apoyo_mat.save()

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
                    if apoyo_mat.cantidad_requerida > 0:
                        inventario, _ = Inventario.objects.get_or_create(material=apoyo_mat.material)
                        inventario.cantidad += apoyo_mat.cantidad_requerida
                        inventario.save()
                    apoyo_mat.delete()
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
                    if apoyo_mat.cantidad_requerida > 0:
                        inv_ant, _ = Inventario.objects.get_or_create(material=apoyo_mat.material)
                        inv_ant.cantidad += apoyo_mat.cantidad_requerida
                        inv_ant.save()

                    nuevo_mat = Material.objects.filter(id=mat_id_nuevo).first()
                    if nuevo_mat:
                        apoyo_mat.material = nuevo_mat
                        apoyo_mat.cantidad_requerida = Decimal("0")

                inventario, _ = Inventario.objects.get_or_create(material=apoyo_mat.material)
                mat_obj = inventario.material
                unidad_str = mat_obj.unidad or "U"

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
                unidad_str = mat_obj.unidad or "U"

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
                            inventario.save()
                        else:
                            inventario.cantidad -= diferencia
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
                            inventario.save()
                        else:
                            inventario.cantidad -= c_inst
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
