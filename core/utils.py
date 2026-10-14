import re
from decimal import Decimal, InvalidOperation


def parse_monto_cop(texto, default=None):
    """Convierte un monto en formato colombiano a Decimal de forma segura.

    - '1.500.000'     -> Decimal('1500000')   (puntos = miles)
    - '1.500.000,50'  -> Decimal('1500000.50') (coma = decimales)
    - '1500000'       -> Decimal('1500000')
    - 'abc' / '' / None -> default (no lanza excepción)
    """
    if texto is None:
        return default
    s = str(texto).strip().replace('$', '').replace(' ', '')
    if not s:
        return default
    if ',' in s:
        s = s.replace('.', '').replace(',', '.')
    else:
        s = s.replace('.', '')
    try:
        return Decimal(s)
    except InvalidOperation:
        return default


def formatear_pesos(valor):
    try:
        valor = int(valor)
        return f"${valor:,}".replace(",", ".")
    except:
        return valor

def limpiar_nombre_archivo(nombre):
    return re.sub(
        r'[\\/*?:"<>|\t\n]',
        '',
        nombre
    ).strip().replace(
        " ",
        "_"
    )