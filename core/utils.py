import re

def formatear_pesos(valor):
    try:
        valor = int(valor)
        return f"${valor:,}".replace(",", ".")
    except:
        return valor3

def limpiar_nombre_archivo(nombre):
    return re.sub(
        r'[\\/*?:"<>|\t\n]',
        '',
        nombre
    ).strip().replace(
        " ",
        "_"
    )