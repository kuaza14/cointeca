from decimal import Decimal
from django import template
from django.template.defaultfilters import register as default_register

register = template.Library()

@register.filter
def pesos_colombianos(valor):
    try:
        return f"{int(valor):,}".replace(",", ".")
    except Exception:
        return valor

def formato_decimal_limpio(text, arg=None):
    if text is None or text == "":
        return ""
    try:
        val = Decimal(str(text).strip().replace(",", "."))
        if arg == 0 or arg == "0":
            return str(int(round(val)))
        max_decimals = None
        if arg is not None and str(arg).lstrip("-").isdigit():
            max_decimals = abs(int(arg))
        if val == val.to_integral():
            return str(int(val))
        if max_decimals is not None and max_decimals > 0:
            val = round(val, max_decimals)
        s = f"{val.normalize():f}"
        if "." in s:
            s = s.rstrip("0").rstrip(".")
        return s
    except Exception:
        try:
            f = float(text)
            if arg == 0 or arg == "0":
                return str(int(round(f)))
            if f.is_integer():
                return str(int(f))
            return f"{f:g}"
        except Exception:
            return str(text)

@register.filter(name="cantidad")
def cantidad(valor):
    return formato_decimal_limpio(valor)

@register.filter(name="formato_decimal")
def formato_decimal(valor, arg=None):
    return formato_decimal_limpio(valor, arg)

# Sobrescribir floatformat globalmente para toda la aplicación
default_register.filters["floatformat"] = formato_decimal_limpio
register.filter("floatformat", formato_decimal_limpio)