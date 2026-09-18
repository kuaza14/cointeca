from decimal import Decimal
from django.db import transaction
from core.models import Apoyo, ApoyoMaterial, ItemManoObra, ApoyoManoObra, Proyecto, Presupuesto

# ==============================================================================
# ⚙️ MOTOR DE CÁLCULO DE MANO DE OBRA PARA INGENIERÍA (COINTECA)
# ==============================================================================

# Reglas de mapeo: Código MO -> Función / Lista de Códigos de Materiales (items)
# Los items corresponden a los números de item en el catálogo oficial de Materiales.

def _sum_mats(cantidades_map, item_codes):
    """Suma las cantidades instaladas para una lista de códigos de material."""
    total = Decimal("0")
    for code in item_codes:
        total += cantidades_map.get(int(code) if str(code).isdigit() else code, Decimal("0"))
    return total

def calcular_mano_obra_para_apoyo(apoyo, preservar_manuales=True):
    """
    Calcula todas las actividades automáticas de Mano de Obra para un apoyo individual,
    basado en los materiales instalados y características técnicas del poste.
    """
    # 1. Obtener materiales instalados en este apoyo
    apoyo_mats = ApoyoMaterial.objects.filter(apoyo=apoyo).select_related('material')
    cantidades_map = {am.material.item: am.cantidad_requerida for am in apoyo_mats}
    cantidades_ret_map = {am.material.item: am.cantidad_retirada for am in apoyo_mats}

    # Detectar si el apoyo es Modernización o Expansión
    # (Por defecto, si tipo_instalacion dice Modernización o hay retiros de luminarias)
    es_modernizacion = (
        "MODERN" in (apoyo.tipo_instalacion or "").upper() or
        apoyo.tipo_estructura == "Modernización"
    )

    # 2. Diccionario de cantidades calculadas por código de Mano de Obra
    calculados = {}

    # --------------------------------------------------------------------------
    # A. POSTES: HUECOS, APLOMADAS, HINCADAS, CONCRETADAS Y TRANSPORTES
    # --------------------------------------------------------------------------
    # Apertura de Hueco 11m a 14m (Cód 192): PRFV 12m (712), Fibra 12m/14m (658, 659), Concreto 12m/14m (654, 655)
    calculados['192'] = _sum_mats(cantidades_map, [712, 658, 659, 654, 655])

    # Apertura de Hueco 8m a 10m (Cód 194): PRFV 8m/10m (710, 711), Fibra 8m/10m (662, 661, 657), Concreto 8m/10m (656, 653)
    calculados['194'] = _sum_mats(cantidades_map, [710, 711, 662, 661, 657, 656, 653])

    # Aplomada Poste Concreto 11 a 14m (Cód 195): Concreto 12m (654) y 14m (655)
    calculados['195'] = _sum_mats(cantidades_map, [654, 655])

    # Aplomada Poste Concreto 8 a 10m (Cód 196): Concreto 8m (656) y 10m (653)
    calculados['196'] = _sum_mats(cantidades_map, [656, 653])

    # Aplomada Poste Metálico o Fibra 11 a 14m (Cód 197): Met 12m/14m (690, 691), Fibra 12m/14m (658, 659)
    calculados['197'] = _sum_mats(cantidades_map, [690, 691, 658, 659])

    # Aplomada Poste Metálico o Fibra 8 a 10m (Cód 198): Met 8m/10m (688, 689), Fibra 8m/10m (661, 662, 657)
    calculados['198'] = _sum_mats(cantidades_map, [688, 689, 661, 662, 657])

    # Concretada Poste Concreto 8 a 12m (Cód 210): Concreto 10m, 12m, 8m (653, 654, 656)
    calculados['210'] = _sum_mats(cantidades_map, [653, 654, 656])

    # Concretada Poste Fibra 8 a 12m (Cód 211): Fibra (657, 658, 661, 662)
    calculados['211'] = _sum_mats(cantidades_map, [657, 658, 661, 662])

    # Hincada Poste Fibra 10 a 12m (Cód 234): Fibra 10m (657), 12m (658)
    calculados['234'] = _sum_mats(cantidades_map, [657, 658])

    # Hincada Poste Fibra 8m (Cód 235): Fibra 8m (662, 661)
    calculados['235'] = _sum_mats(cantidades_map, [662, 661])

    # Hincada Poste Concreto 14m (Cód 236): Concreto 14m (655)
    calculados['236'] = _sum_mats(cantidades_map, [655])

    # Hincada Poste Concreto 8 a 12m (Cód 237): Concreto (656, 654, 653)
    calculados['237'] = _sum_mats(cantidades_map, [656, 654, 653])

    # Pintada Nodo inc. Pintura (Cód 278): Suma de cualquier poste instalado
    calculados['278'] = _sum_mats(cantidades_map, [
        710, 711, 712, 688, 689, 690, 691, 692, 662, 661, 660, 659, 658, 657, 656, 655, 654, 653
    ])

    # Transporte Poste Concreto 12m (Cód 288)
    calculados['288'] = _sum_mats(cantidades_map, [654])

    # Transporte Poste Metálico 4 a 12m (Cód 290): Metálico (688, 689, 690)
    calculados['290'] = _sum_mats(cantidades_map, [688, 689, 690])

    # Transporte Poste Concreto 14m (Cód 298)
    calculados['298'] = _sum_mats(cantidades_map, [655])

    # --------------------------------------------------------------------------
    # B. LUMINARIAS, PROYECTORES Y TELECELDAS
    # --------------------------------------------------------------------------
    # Instalación Luminarias en Camioneta (Cód 268): LED 25W, 40W, 50W, 60W, 75W (693 a 697)
    tot_lum_camioneta = _sum_mats(cantidades_map, [693, 694, 695, 696, 697])
    calculados['268'] = tot_lum_camioneta

    # Instalación Luminarias en Canasta (Cód 269): LED 95W, 110W, 120W, 150W, 190W (698 a 702)
    tot_lum_canasta = _sum_mats(cantidades_map, [698, 699, 700, 701, 702])
    calculados['269'] = tot_lum_canasta

    # Instalación de Reflector (Cód 259): Proy LED 50W, 90W, 140W, 190W (703 a 706)
    tot_proyectores = _sum_mats(cantidades_map, [703, 704, 705, 706])
    calculados['259'] = tot_proyectores

    # Desmonte Luminarias en Camioneta (Cód 225): Si es modernización
    if es_modernizacion:
        calculados['225'] = tot_lum_camioneta
        calculados['222'] = tot_lum_canasta

    # Desmonte de Cofre (Cód 221)
    calculados['221'] = tot_proyectores

    # Conexión Cable a Tierra Luminaria / Conector SPT (Cód 213)
    calculados['213'] = tot_lum_camioneta + tot_lum_canasta + tot_proyectores

    # Transporte Luminarias y Proyectores (Cód 287)
    calculados['287'] = tot_lum_camioneta + tot_lum_canasta + tot_proyectores

    # --------------------------------------------------------------------------
    # C. CABLES Y ACOMETIDAS (CON REGLA DE HOLGURA +5%)
    # --------------------------------------------------------------------------
    # Cable encauchado adosado (Cód 241): Item 590
    cant_cable_encauchado = _sum_mats(cantidades_map, [590])
    calculados['241'] = cant_cable_encauchado * Decimal("1.05") if cant_cable_encauchado > 0 else Decimal("0")

    # Cable Secundario 14 en Ducto (Cód 242): Alambre THHN 14 (535, 536)
    cant_thhn = _sum_mats(cantidades_map, [535, 536])
    calculados['242'] = cant_thhn * Decimal("1.05") if cant_thhn > 0 else Decimal("0")

    # Transp / Inst Cable TPX 2x4+1x4 (Cód 323): Item 589
    cant_tpx_4 = _sum_mats(cantidades_map, [589])
    calculados['323'] = cant_tpx_4 * Decimal("1.05") if cant_tpx_4 > 0 else Decimal("0")

    # Transp / Inst Cable TPX 2x2+1x2 (Cód 324): Item 588
    cant_tpx_2 = _sum_mats(cantidades_map, [588])
    calculados['324'] = cant_tpx_2 * Decimal("1.05") if cant_tpx_2 > 0 else Decimal("0")

    # Transp / Inst Cable TPX 2x1/0+1x1/0 (Cód 325): Item 587
    cant_tpx_10 = _sum_mats(cantidades_map, [587])
    calculados['325'] = cant_tpx_10 * Decimal("1.05") if cant_tpx_10 > 0 else Decimal("0")

    # Transporte de Cables (Cód 294): Suma de cables con holgura
    tot_cables_transporte = (
        calculados['241'] + calculados['242'] + calculados['323'] + calculados['324'] + calculados['325']
    )
    calculados['294'] = tot_cables_transporte

    # --------------------------------------------------------------------------
    # D. HERRAJES, BRAZOS, CRUCETAS, ACCESORIOS Y TRANSPORTES
    # --------------------------------------------------------------------------
    # Transporte Collarín / Abrazaderas (Cód 291): Abrazaderas (518 a 532)
    tot_abrazaderas = _sum_mats(cantidades_map, list(range(518, 533)))
    calculados['291'] = tot_abrazaderas

    # Corona de Seguridad (Cód 248): Abrazaderas corona 6", 7", 10" (524, 525, 526)
    calculados['248'] = _sum_mats(cantidades_map, [524, 525, 526])

    # Transporte Brazos 1 1/2" hasta 3m (Cód 292): Brazos (576, 577, 578, 579)
    calculados['292'] = _sum_mats(cantidades_map, [576, 577, 578, 579])

    # Transporte Brazos 2 1/2" hasta 6m (Cód 293): Brazo galv 2 1/2x6m (576)
    calculados['293'] = _sum_mats(cantidades_map, [576])

    # Transporte Crucetas hasta 3m (Cód 295): Cruceta metálica (623)
    calculados['295'] = _sum_mats(cantidades_map, [623])

    # Vestida de Crucetas Conjunto Secundario (Cód 322): Cruceta (623)
    calculados['322'] = _sum_mats(cantidades_map, [623])

    # Transporte Diagonales (Cód 296): Angular en V (537)
    calculados['296'] = _sum_mats(cantidades_map, [537])

    # Transporte Percha con Aislador (Cód 301): Perchas (648, 649)
    calculados['301'] = _sum_mats(cantidades_map, [648, 649])

    # Vestida Conjunto 1 o 2 Perchas (Cód 320): Percha (649) y Perfil ranurado (650)
    calculados['320'] = _sum_mats(cantidades_map, [649, 650])

    # Cubierta Gel Conector GHFC (Cód 257): Empalmes gel (631, 632, 633, 634)
    calculados['257'] = _sum_mats(cantidades_map, [631, 632, 633, 634])

    # Aterrizajes Secundarios (Cód 249): Varilla cooperweld (686)
    calculados['249'] = _sum_mats(cantidades_map, [686])

    # Kit Puesta a Tierra Cinta Metálica (Cód 266): Kit acero inox (643)
    calculados['266'] = _sum_mats(cantidades_map, [643])

    # Transporte Varilla Tierra / Kit Tierra (Cód 319): Varilla (686) + Kit (643)
    calculados['319'] = _sum_mats(cantidades_map, [686, 643])

    # Transporte Tubería hasta 4" (Cód 318): Tuberías (672 a 681) + tornillos (672)
    calculados['318'] = _sum_mats(cantidades_map, list(range(672, 682)))

    # Cajas AP, Tapas y Soldadura: Tapa caja AP (670)
    cant_tapa = _sum_mats(cantidades_map, [670])
    calculados['280'] = cant_tapa # Recuperación tapa
    calculados['300'] = cant_tapa # Transporte tapa
    calculados['274'] = cant_tapa # Soldadura 4 cordones

    # 3. Guardar en Base de Datos para este apoyo
    items_mo_dict = {item.codigo: item for item in ItemManoObra.objects.filter(codigo__in=calculados.keys())}

    guardados = 0
    for code, cant in calculados.items():
        if cant <= 0:
            # Si el cálculo da 0, eliminar el registro automático previo si existía
            ApoyoManoObra.objects.filter(apoyo=apoyo, item_mano_obra__codigo=code, origen=ApoyoManoObra.Origen.CALCULADO).delete()
            continue

        item_obj = items_mo_dict.get(code)
        if not item_obj:
            continue

        amo = ApoyoManoObra.objects.filter(apoyo=apoyo, item_mano_obra=item_obj).first()
        if amo:
            if amo.origen == ApoyoManoObra.Origen.MANUAL and preservar_manuales:
                continue # No sobreescribir ajustes manuales del usuario
            amo.cantidad = cant
            amo.origen = ApoyoManoObra.Origen.CALCULADO
            amo.save()
        else:
            ApoyoManoObra.objects.create(
                apoyo=apoyo,
                item_mano_obra=item_obj,
                cantidad=cant,
                origen=ApoyoManoObra.Origen.CALCULADO
            )
        guardados += 1

    return guardados


@transaction.atomic
def calcular_mano_obra_proyecto_completo(proyecto, preservar_manuales=True):
    """
    Recorre todos los apoyos del proyecto, calcula su Mano de Obra y actualiza el Presupuesto.
    """
    apoyos = Apoyo.objects.filter(proyecto=proyecto)
    total_guardados = 0
    for ap in apoyos:
        total_guardados += calcular_mano_obra_para_apoyo(ap, preservar_manuales=preservar_manuales)

    # Actualizar Presupuesto del Proyecto
    actualizar_presupuesto_proyecto(proyecto)
    return total_guardados


def actualizar_presupuesto_proyecto(proyecto):
    """
    Calcula el total de Materiales y el total de Mano de Obra y actualiza el modelo Presupuesto.
    """
    # 1. Total Materiales (si tienen precio o coste definido)
    # 2. Total Mano de Obra
    apoyos_ids = Apoyo.objects.filter(proyecto=proyecto).values_list('id', flat=True)
    manos_obra = ApoyoManoObra.objects.filter(apoyo_id__in=apoyos_ids).select_related('item_mano_obra')

    total_mo = Decimal("0")
    for mo in manos_obra:
        total_mo += mo.cantidad * mo.item_mano_obra.valor_unitario

    presupuesto, _ = Presupuesto.objects.get_or_create(proyecto=proyecto)
    presupuesto.valor_mano_obra = total_mo
    presupuesto.valor_total = presupuesto.valor_materiales + presupuesto.valor_mano_obra + presupuesto.otros_costos
    presupuesto.save()

    return presupuesto
