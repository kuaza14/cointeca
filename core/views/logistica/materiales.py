from django.shortcuts import render, redirect, get_object_or_404
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from core.models import Material, Inventario, DevolucionMaterialProyecto, ApoyoMaterial, MovimientoInventario
from core.helpers.inventario_historial import registrar_movimiento_inventario


@login_required
def materiales_home(request):
    """
    Catálogo e Inventario General de Bodega Central.
    Permite consultar existencias, auditar historial de movimientos, ajustar stock y crear nuevos materiales.
    """
    if request.method == "POST":
        accion = request.POST.get("accion")

        # 1. Ajustar o cargar stock a un material existente
        if accion == "actualizar_stock":
            material_id = request.POST.get("material_id")
            nueva_cantidad_str = request.POST.get("cantidad", "0")
            nueva_unidad = request.POST.get("unidad", "").strip()
            observacion = request.POST.get("observacion", "").strip()

            if material_id:
                try:
                    material = get_object_or_404(Material, id=material_id)
                    nueva_cantidad = Decimal(nueva_cantidad_str.strip() or "0")

                    if nueva_unidad:
                        if nueva_unidad.upper() == "U":
                            nueva_unidad = "UN"
                        material.unidad = nueva_unidad
                        material.save()

                    inventario, _ = Inventario.objects.get_or_create(material=material)
                    stock_anterior = inventario.cantidad or Decimal("0")
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
                except (ValueError, TypeError):
                    pass

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
                    item_num = int(item_str) if item_str.isdigit() else (Material.objects.count() + 1)
                    material = Material.objects.create(
                        item=item_num,
                        descripcion=descripcion,
                        unidad=unidad or "UN"
                    )
                    cant_inicial = Decimal(cantidad_str.strip() or "0")
                    Inventario.objects.create(
                        material=material,
                        cantidad=cant_inicial
                    )
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
                except Exception:
                    pass

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