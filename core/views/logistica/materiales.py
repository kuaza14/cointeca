from django.shortcuts import render, redirect, get_object_or_404
from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Max, ProtectedError
from core.models import Material, Inventario, DevolucionMaterialProyecto, ApoyoMaterial, MovimientoInventario
from core.helpers.inventario_historial import registrar_movimiento_inventario


def _parse_decimal(valor):
    """Acepta '12.5' o '12,5' (coma decimal es-CO)."""
    return Decimal(str(valor).strip().replace(",", ".") or "0")


@login_required
@transaction.atomic
def materiales_home(request):
    """
    Catálogo e Inventario General de Bodega Central.
    Permite consultar existencias, auditar historial de movimientos, ajustar stock y crear nuevos materiales.
    """
    if request.method == "POST":
        accion = request.POST.get("accion")

        # 1. Ajustar o cargar stock a un material existente (y editar descripción / ítem)
        if accion == "actualizar_stock":
            material_id = request.POST.get("material_id")
            nueva_cantidad_str = request.POST.get("cantidad", "0")
            nueva_unidad = request.POST.get("unidad", "").strip()
            nueva_descripcion = request.POST.get("descripcion", "").strip()
            nuevo_item_str = request.POST.get("item", "").strip()
            observacion = request.POST.get("observacion", "").strip()

            if material_id:
                try:
                    material = get_object_or_404(Material, id=material_id)
                    nueva_cantidad = _parse_decimal(nueva_cantidad_str)

                    # 1.1 Modificar descripción si se envió
                    if nueva_descripcion:
                        material.descripcion = nueva_descripcion

                    # 1.2 Modificar ítem si se envió y verificar duplicados
                    if nuevo_item_str:
                        if not nuevo_item_str.isdigit():
                            messages.error(request, "⚠️ El número de ítem debe ser un número entero.")
                            return redirect("materiales_home")
                        nuevo_item = int(nuevo_item_str)
                        if nuevo_item != material.item:
                            duplicado = Material.objects.filter(item=nuevo_item).exclude(id=material.id).first()
                            if duplicado:
                                messages.error(
                                    request,
                                    f"⚠️ Aviso: El ítem #{nuevo_item} ya está registrado para '{duplicado.descripcion}'. Elige otro número de ítem."
                                )
                                return redirect("materiales_home")
                            material.item = nuevo_item

                    if nueva_unidad:
                        if nueva_unidad.upper() == "U":
                            nueva_unidad = "UN"
                        material.unidad = nueva_unidad

                    material.save()

                    inventario, _ = Inventario.objects.get_or_create(
                        material=material,
                        defaults={"cantidad": Decimal("0")}
                    )
                    inventario = Inventario.objects.select_for_update().get(pk=inventario.pk)
                    stock_anterior = inventario.cantidad if inventario.cantidad is not None else Decimal("0")
                    inventario.cantidad = nueva_cantidad
                    inventario.save()

                    diferencia = nueva_cantidad - stock_anterior
                    registrar_movimiento_inventario(
                        material=material,
                        tipo_movimiento=MovimientoInventario.Tipos.AJUSTE,
                        cantidad=diferencia,
                        stock_anterior=stock_anterior,
                        stock_resultante=nueva_cantidad,
                        usuario=request.user,
                        detalle_origen_destino="Bodega Central (Ajuste Físico)",
                        observacion=observacion or "Ajuste manual de existencias físicas en Bodega"
                    )
                    messages.success(
                        request,
                        f"Material #{material.item} '{material.descripcion}' actualizado correctamente. Existencia: {nueva_cantidad} {material.unidad}."
                    )
                except (ValueError, TypeError, InvalidOperation):
                    messages.error(request, "La cantidad ingresada no es un número válido.")
                except Exception as e:
                    messages.error(request, f"Error al actualizar la existencia: {e}")

            return redirect("materiales_home")

        # 2. Crear un nuevo material en el catálogo
        elif accion == "crear_material":
            item_str = request.POST.get("item", "").strip()
            descripcion = request.POST.get("descripcion", "").strip()
            unidad = request.POST.get("unidad", "UN").strip()
            if unidad.upper() == "U":
                unidad = "UN"
            cantidad_str = request.POST.get("cantidad_inicial", "0")

            if descripcion:
                try:
                    if item_str:
                        if not item_str.isdigit():
                            messages.error(request, "⚠️ El número de ítem debe ser un número entero.")
                            return redirect("materiales_home")
                        item_num = int(item_str)
                        duplicado = Material.objects.filter(item=item_num).first()
                        if duplicado:
                            messages.error(
                                request,
                                f"⚠️ Aviso: El ítem #{item_num} ya existe en el catálogo ('{duplicado.descripcion}'). No se puede duplicar."
                            )
                            return redirect("materiales_home")
                    else:
                        item_num = (Material.objects.aggregate(
                            max_item=Max("item")
                        )["max_item"] or 0) + 1

                    material = Material.objects.create(
                        item=item_num,
                        descripcion=descripcion,
                        unidad=unidad or "UN"
                    )
                    cant_inicial = _parse_decimal(cantidad_str)
                    inv_obj, _ = Inventario.objects.get_or_create(
                        material=material,
                        defaults={"cantidad": cant_inicial}
                    )
                    inv_obj.cantidad = cant_inicial
                    inv_obj.save()
                    if cant_inicial != 0:
                        registrar_movimiento_inventario(
                            material=material,
                            tipo_movimiento=MovimientoInventario.Tipos.ENTRADA,
                            cantidad=cant_inicial,
                            stock_anterior=Decimal("0"),
                            stock_resultante=cant_inicial,
                            usuario=request.user,
                            detalle_origen_destino="Bodega Central (Creación de Material)",
                            observacion="Carga de saldo inicial de material nuevo"
                        )
                    messages.success(request, f"Material #{item_num} '{descripcion}' creado correctamente.")
                except InvalidOperation:
                    messages.error(request, "La cantidad inicial no es un número válido.")
                except IntegrityError:
                    messages.error(request, f"Ya existe un material con el ítem #{item_str}.")
                except Exception as e:
                    messages.error(request, f"No se pudo crear el material: {e}")
            else:
                messages.warning(request, " Debes indicar la descripción del material.")

            return redirect("materiales_home")

        # 3. Eliminar un material del catálogo
        elif accion == "eliminar_material":
            material_id = request.POST.get("material_id")
            if material_id:
                try:
                    material = get_object_or_404(Material, id=material_id)
                    item_num = material.item
                    desc_mat = material.descripcion

                    if hasattr(material, "apoyos") and material.apoyos.filter(cantidad_requerida__gt=0).exists():
                        messages.warning(
                            request,
                            f"⚠️ No se puede eliminar el material #{item_num} '{desc_mat}' porque ya está asignado a postes o nodos en proyectos."
                        )
                    else:
                        material.delete()
                        messages.success(request, f"🗑️ Material #{item_num} '{desc_mat}' eliminado correctamente del catálogo.")
                except ProtectedError:
                    messages.warning(
                        request,
                        f"⚠️ No se puede eliminar el material #{material.item} '{material.descripcion}' porque tiene registros históricos o actas vinculadas."
                    )
                except Exception as e:
                    messages.error(request, f"Error al eliminar material: {e}")

            return redirect("materiales_home")

    materiales = list(
        Material.objects.select_related("inventario").order_by("descripcion")
)
    total_materiales = len(materiales)

    devoluciones_recientes = (
        DevolucionMaterialProyecto.objects.prefetch_related("proyecto", "detalles__material")
.order_by("-fecha", "-id")
)

    retiros_apoyos = (
        ApoyoMaterial.objects.filter(cantidad_retirada__gt=0)
.select_related("apoyo", "apoyo__proyecto", "material")
.order_by("-apoyo__id", "material__descripcion")
)

    movimientos = (
        MovimientoInventario.objects.select_related(
            "material", "usuario", "proyecto", "apoyo"
).order_by("-fecha", "-id")[:200]
)

    total_movimientos = MovimientoInventario.objects.count()

    return render(
        request,
        "logistica/materiales/materiales_home.html",
        {
            "materiales": materiales,
            "total_materiales": total_materiales,
            "devoluciones_recientes": devoluciones_recientes,
            "retiros_apoyos": retiros_apoyos,
            "movimientos": movimientos,
            "total_movimientos": total_movimientos,
        }
)