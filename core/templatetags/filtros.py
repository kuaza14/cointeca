from django import template

register = template.Library()

@register.filter
def pesos_colombianos(valor):
    try:
        return f"{int(valor):,}".replace(",", ".")
    except:
        return valor