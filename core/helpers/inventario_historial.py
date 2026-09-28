from decimal import Decimal
from django.utils import timezone
from core.models import MovimientoInventario

def registrar_movimiento_inventario(
    material,
    tipo_movimiento,
    cantidad,
    stock_anterior,
    stock_resultante,
    usuario=None,
    proyecto=None,
    apoyo=None,
    detalle_origen_destino="",
    observacion=""
):
    """
    Registra de forma segura un movimiento en el Kardex / Historial de Bodega Central.
    """
    try:
        user_nombre = ""
        user_obj = None
        if usuario:
            if hasattr(usuario, "is_authenticated") and usuario.is_authenticated:
                user_obj = usuario
                user_nombre = usuario.get_full_name() or usuario.username
            else:
                user_nombre = str(usuario)

        return MovimientoInventario.objects.create(
            material=material,
            tipo_movimiento=tipo_movimiento,
            cantidad=Decimal(str(cantidad)),
            stock_anterior=Decimal(str(stock_anterior)),
            stock_resultante=Decimal(str(stock_resultante)),
            usuario=user_obj,
            usuario_nombre=user_nombre,
            proyecto=proyecto,
            apoyo=apoyo,
            detalle_origen_destino=detalle_origen_destino[:255] if detalle_origen_destino else "",
            observacion=observacion or "",
            fecha=timezone.now()
        )
    except Exception as e:
        print(f"Error al registrar movimiento de inventario: {e}")
        return None
