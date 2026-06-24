def formatear_pesos(valor):
    try:
        valor = int(valor)
        return f"${valor:,}".replace(",", ".")
    except:
        return valor3