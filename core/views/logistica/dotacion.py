import os

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from openpyxl import load_workbook

from core.models import Empleado, DotacionEmpleado


@login_required
def dotacion_home(request):

    empleados = Empleado.objects.all().order_by("nombre_completo")

    return render(
        request,
        "logistica/dotacion/dotacion_home.html",
        {
            "lista_empleados": empleados,
        }
    )


@login_required
def detalle_dotacion(request, id):

    empleado = get_object_or_404(
        Empleado,
        id=id
    )

    if request.method == "POST":

        registro_id = request.POST.get("registro_id")

        fecha = request.POST.get("fecha_entrega")
        observacion = request.POST.get("observacion")

        # EDITAR
        accion = request.POST.get("accion")

        eliminar_id = request.POST.get("eliminar_id")

        if accion == "eliminar":

            registro = get_object_or_404(
                DotacionEmpleado,
                id=eliminar_id
            )

            registro.delete()

        if accion == "editar":

            registro = get_object_or_404(
                DotacionEmpleado,
                id=registro_id
            )

            registro.fecha_entrega = fecha
            registro.observacion = observacion

            registro.save()

        # REGISTRAR
        elif accion == "registrar":

            DotacionEmpleado.objects.create(
                empleado=empleado,
                fecha_entrega=fecha,
                observacion=observacion,
            )

        return redirect(
            "detalle_dotacion",
            id=empleado.id
        )

    historial = empleado.dotaciones.all().order_by("-fecha_entrega")

    ultima = historial.first()

    return render(
        request,
        "logistica/dotacion/detalle_dotacion.html",
        {
            "empleado": empleado,
            "historial": historial,
            "ultima": ultima,
        }
    )


@login_required
def generar_dotacion(request, id):

    empleado = get_object_or_404(
        Empleado,
        id=id
    )

    ruta = os.path.join(
        settings.BASE_DIR,
        "plantillas_excel",
        "dotacion.xlsx"
    )

    libro = load_workbook(ruta)

    hoja = libro.active

    hoja["B8"] = f"NOMBRE COMPLETO: {empleado.nombre_completo}"
    hoja["F8"] = f"N° CC: {empleado.documento}"

    hoja["B9"] = f"CARGO: {empleado.cargo}"
    hoja["F9"] = f"AREA: {empleado.area}"

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    response["Content-Disposition"] = (
        f'attachment; filename="Dotacion_{empleado.nombre_completo}.xlsx"'
    )

    libro.save(response)

    return response
