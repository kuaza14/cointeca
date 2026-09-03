from django.shortcuts import render, redirect, get_object_or_404
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from core.models import Material, Inventario


@login_required
def materiales_home(request):
    """
    Catálogo e Inventario General de Bodega Central.
    Permite consultar existencias, ajustar stock de bodega y agregar nuevos materiales.
    """
    if request.method == "POST":
        accion = request.POST.get("accion")

        # 1. Ajustar o cargar stock a un material existente
        if accion == "actualizar_stock":
            material_id = request.POST.get("material_id")
            nueva_cantidad_str = request.POST.get("cantidad", "0")
            nueva_unidad = request.POST.get("unidad", "").strip()

            if material_id:
                try:
                    material = get_object_or_404(Material, id=material_id)
                    nueva_cantidad = Decimal(nueva_cantidad_str.strip() or "0")

                    if nueva_unidad:
                        material.unidad = nueva_unidad
                        material.save()

                    inventario, _ = Inventario.objects.get_or_create(material=material)
                    inventario.cantidad = max(Decimal("0"), nueva_cantidad)
                    inventario.save()
                except (ValueError, TypeError):
                    pass

            return redirect("materiales_home")

        # 2. Crear un nuevo material en el catálogo
        elif accion == "crear_material":
            item_str = request.POST.get("item", "").strip()
            descripcion = request.POST.get("descripcion", "").strip()
            unidad = request.POST.get("unidad", "U").strip()
            cantidad_str = request.POST.get("cantidad_inicial", "0")

            if descripcion:
                try:
                    item_num = int(item_str) if item_str.isdigit() else (Material.objects.count() + 1)
                    material = Material.objects.create(
                        item=item_num,
                        descripcion=descripcion,
                        unidad=unidad
                    )
                    cant_inicial = Decimal(cantidad_str.strip() or "0")
                    Inventario.objects.create(
                        material=material,
                        cantidad=max(Decimal("0"), cant_inicial)
                    )
                except Exception:
                    pass

            return redirect("materiales_home")

    materiales = Material.objects.select_related(
        "inventario"
    ).order_by("descripcion")

    return render(
        request,
        "logistica/materiales/materiales_home.html",
        {
            "materiales": materiales,
            "total_materiales": materiales.count(),
        }
    )