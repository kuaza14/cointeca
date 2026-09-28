from core.models import IndicadorEstrategico

INDICADORES_DEFAULT = [
    {
        "perspectiva": "financiera",
        "nombre": "Margen por Proyecto",
        "definicion": "(Utilidad Bruta / Valor Contrato) * 100",
        "meta_anual": "> 25%",
        "frecuencia": "mensual",
    },
    {
        "perspectiva": "financiera",
        "nombre": "Eficacia de Recaudo",
        "definicion": "(Cartera Cobrada / Cartera Facturada) * 100",
        "meta_anual": "> 90%",
        "frecuencia": "mensual",
    },
    {
        "perspectiva": "comercial",
        "nombre": "Tasa de Cierre Solar",
        "definicion": "(Proyectos Solar Cerrados / Propuestas Enviadas)",
        "meta_anual": "15%",
        "frecuencia": "trimestral",
    },
    {
        "perspectiva": "comercial",
        "nombre": "Ticket Promedio",
        "definicion": "Valor total facturado / Número de clientes",
        "meta_anual": "Incrementar 10%",
        "frecuencia": "semestral",
    },
    {
        "perspectiva": "operativa",
        "nombre": "Éxito RETIE",
        "definicion": "Visitas de certificación aprobadas sin hallazgos",
        "meta_anual": "100%",
        "frecuencia": "por_proyecto",
    },
    {
        "perspectiva": "operativa",
        "nombre": "Eficiencia en Redes",
        "definicion": "(Horas Hombre Estimadas / Horas Reales)",
        "meta_anual": "> 0.95",
        "frecuencia": "mensual",
    },
    {
        "perspectiva": "cliente",
        "nombre": "Índice de Fidelidad",
        "definicion": "% Clientes que repiten servicio (ej. Mantenimiento)",
        "meta_anual": "30%",
        "frecuencia": "anual",
    },
    {
        "perspectiva": "cliente",
        "nombre": "NPS (Satisfacción)",
        "definicion": "Calificación de servicio pos-entrega (1-10)",
        "meta_anual": "> 8.5",
        "frecuencia": "por_proyecto",
    },
    {
        "perspectiva": "aprendizaje",
        "nombre": "Capacitación Técnica",
        "definicion": "Horas de formación en nuevas normas/tecnologías",
        "meta_anual": "40h / Ingeniero",
        "frecuencia": "semestral",
    },
]

def sembrar_indicadores_oficiales():
    creados = 0
    for item in INDICADORES_DEFAULT:
        _, created = IndicadorEstrategico.objects.get_or_create(
            nombre=item["nombre"],
            defaults={
                "perspectiva": item["perspectiva"],
                "definicion": item["definicion"],
                "meta_anual": item["meta_anual"],
                "frecuencia": item["frecuencia"],
            }
        )
        if created:
            creados += 1
    return creados
