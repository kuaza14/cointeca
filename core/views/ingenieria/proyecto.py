from django.shortcuts import render, redirect, get_object_or_404
from decimal import Decimal
from django.db.models import Sum
from core.models import Proyecto, Apoyo, Material, ApoyoMaterial
from django.db import transaction
from django.contrib.auth.decorators import login_required


@login_required
def ingenieria_inicio(request):
    return render(
        request,
        "ingenieria/ingenieria_inicio.html"
    )

@login_required
def lista_proyectos(request):
    proyectos = Proyecto.objects.all().order_by("-id")
    return render(
        request,
        "ingenieria/proyecto/lista.html",
        {
            "proyectos": proyectos
        }
    )

@login_required
def crear_proyecto(request):
    if request.method == "POST":
        Proyecto.objects.create(
            numero_emcali=request.POST.get("numero_emcali"),
            tipo=request.POST.get("tipo")
        )
        return redirect("lista_proyectos")
    return redirect("lista_proyectos")

@login_required
def detalle_proyecto(request, id):
    proyecto = get_object_or_404(Proyecto, id=id)

    apoyos = Apoyo.objects.filter(
        proyecto=proyecto
    ).order_by("numero_apoyo", "id")

    # 1. Obtener todos los materiales únicos asignados a los apoyos de este proyecto
    apoyo_materiales = ApoyoMaterial.objects.filter(
        apoyo__proyecto=proyecto
    ).select_related("material")

    materiales_ids = apoyo_materiales.values_list('material_id', flat=True).distinct()
    materiales_columnas = list(Material.objects.filter(id__in=materiales_ids).order_by("descripcion"))

    cantidades_map = {}
    for am in apoyo_materiales:
        cantidades_map[(am.apoyo_id, am.material_id)] = am.cantidad_requerida

    # 3. Construir filas de la matriz estilo Excel (Filas = Apoyos/Nodos, Columnas = Materiales)
    filas_matriz = []
    totales_por_columna = {mat.id: Decimal("0") for mat in materiales_columnas}

    for ap in apoyos:
        celdas = []
        for mat in materiales_columnas:
            cant = cantidades_map.get((ap.id, mat.id), Decimal("0"))
            celdas.append({
                "material": mat,
                "cantidad": cant,
            })
            totales_por_columna[mat.id] += cant

        filas_matriz.append({
            "apoyo": ap,
            "celdas": celdas,
        })

    # 4. Fila de Totales Generales
    fila_totales = []
    for mat in materiales_columnas:
        fila_totales.append({
            "material": mat,
            "total": totales_por_columna.get(mat.id, Decimal("0")),
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

        Apoyo.objects.create(
            proyecto=proyecto,
            numero_apoyo=numero_apoyo,
            nodo=request.POST.get("nodo", "").strip(),
            estado="Pendiente"
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
    ).select_related("material")

    materiales_catalogo = Material.objects.all().order_by("descripcion")

    if request.method == "POST":

        # ==========================================
        # ELIMINAR MATERIAL
        # ==========================================
        accion = request.POST.get("accion")

        if accion == "eliminar_material":
            item_id = request.POST.get("item_id")

            if item_id:
                ApoyoMaterial.objects.filter(
                    id=item_id,
                    apoyo=apoyo
                ).delete()

            return redirect("detalle_apoyo", apoyo_id=apoyo.id)

        # ==========================================
        # GUARDAR DATOS DEL APOYO
        # ==========================================
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

        apoyo.nombre_quien_ejecuta = request.POST.get(
            "nombre_quien_ejecuta",
            ""
        ).strip()

        apoyo.observacion = request.POST.get(
            "observacion",
            ""
        ).strip()

        apoyo.save()

        # ==========================================
        # GUARDAR MATERIALES
        # ==========================================

        materiales_ids = request.POST.getlist("material_id[]")
        cantidades = request.POST.getlist("cantidad[]")

        for material_id, cantidad in zip(
            materiales_ids,
            cantidades
        ):

            if not material_id or not cantidad:
                continue

            try:
                cant_decimal = Decimal(cantidad)

                if cant_decimal <= 0:
                    continue

                ApoyoMaterial.objects.update_or_create(
                    apoyo=apoyo,
                    material_id=material_id,
                    defaults={
                        "cantidad_requerida": cant_decimal
                    }
                )

            except (ValueError, TypeError, ArithmeticError):
                continue

        # ==========================================
        # DECIDIR A DÓNDE VOLVER
        # ==========================================

        if "guardar_y_volver" in request.POST:
            return redirect(
                "detalle_proyecto",
                id=apoyo.proyecto.id
            )

        return redirect(
            "detalle_apoyo",
            apoyo_id=apoyo.id
        )

    return render(
        request,
        "ingenieria/apoyos/detalle_apoyo.html",
        {
            "apoyo": apoyo,
            "materiales_asociados": materiales_asociados,
            "materiales_catalogo": materiales_catalogo,
        }
    )

@login_required
def eliminar_apoyo(request, apoyo_id):
    apoyo = get_object_or_404(
        Apoyo,
        id=apoyo_id
    )

    proyecto_id = apoyo.proyecto.id

    if request.method == "POST":
        apoyo.delete()

    return redirect(
        "detalle_proyecto",
        id=proyecto_id
    )