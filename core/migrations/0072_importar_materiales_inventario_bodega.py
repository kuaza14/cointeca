from decimal import Decimal
from django.db import migrations
from django.utils import timezone


def cargar_materiales_e_inventario(apps, schema_editor):
    Material = apps.get_model('core', 'Material')
    Inventario = apps.get_model('core', 'Inventario')
    MovimientoInventario = apps.get_model('core', 'MovimientoInventario')
    User = apps.get_model('auth', 'User')

    admin_user = User.objects.filter(is_superuser=True).first() or User.objects.first()

    # 44 Nuevos materiales con consecutivo 161 a 204
    NUEVOS_MATERIALES = [
        (161, 'Abrazadera para TRAFO 7" - 180 mm', 'UN', Decimal('0')),
        (162, 'Aislador Line Post 15 KV', 'UN', Decimal('0')),
        (163, 'Borna terminal tipo pala de ojo - 266.8 MCM', 'UN', Decimal('0')),
        (164, 'Brazo antibalanceo polimérico', 'UN', Decimal('1.00')),
        (165, 'Cable ecológico semiaislado 1/0 AWG', 'MT', Decimal('75.00')),
        (166, 'Cable ecológico semiaislado 4/0 AWG', 'MT', Decimal('0')),
        (167, 'Cable ecológico semiaislado 266.8 KCM', 'MT', Decimal('685.00')),
        (168, 'Cable monopolar No. 2', 'MT', Decimal('0')),
        (169, 'Cinta aislante Super 33', 'MT', Decimal('0')),
        (170, 'Cruceta autosoportada 120 cm', 'UN', Decimal('9.00')),
        (171, 'Conector tipo ampar', 'UN', Decimal('44.00')),
        (172, 'Conector AP2', 'UN', Decimal('27.00')),
        (173, 'Varilla roscada 5/8"', 'UN', Decimal('4.00')),
        (174, 'Conector perforación 16-35 a 1/0-2', 'UN', Decimal('0')),
        (175, 'Cuchilla Chance', 'UN', Decimal('0')),
        (176, 'Cuchilla tipo cortacircuito EATON - 600 Amp', 'UN', Decimal('3.00')),
        (177, 'Diagonal angular bandera', 'UN', Decimal('16.00')),
        (178, 'Espárrago con ojo 5/8"', 'UN', Decimal('0')),
        (179, 'Fusible 9 Amp', 'UN', Decimal('0')),
        (180, 'Herraje L para protecciones', 'UN', Decimal('27.00')),
        (181, 'Kit puesta a tierra Hilo Guarda', 'UN', Decimal('0')),
        (182, 'Pararrayo 15 KV - DPS', 'UN', Decimal('15.00')),
        (183, 'Platina metálica extensión doble aislador', 'UN', Decimal('0')),
        (184, 'Poste metálico galvanizado 16m x 1350 kg', 'UN', Decimal('0')),
        (185, 'Riel perfil en I', 'UN', Decimal('0')),
        (186, 'Terminal ponchar 2 huecos tipo pala 266.8 MCM', 'UN', Decimal('0')),
        (187, 'Terminal ponchar 2 huecos tipo pala 4/0 AWG', 'UN', Decimal('0')),
        (188, 'Tornillo bronce 1/2" x 1-1/2"', 'UN', Decimal('0')),
        (189, 'Varilla puesta a tierra Copperweld 5/8" x 2.4 m', 'UN', Decimal('15.00')),
        (190, 'Cañuelas para cortacircuito', 'UN', Decimal('10.00')),
        (191, 'Pie de amigo para cruceta', 'UN', Decimal('0')),
        (192, 'Tubo conduit EMT 4"', 'UN', Decimal('0')),
        (193, 'Tubo conduit EMT 2"', 'UN', Decimal('0')),
        (194, 'Tubo conduit PVC 2"', 'UN', Decimal('0')),
        (195, 'Tubo conduit PVC 3"', 'UN', Decimal('4.00')),
        (196, 'Curva PVC 6"', 'UN', Decimal('5.00')),
        (197, 'Curva PVC 2"', 'UN', Decimal('0')),
        (198, 'Tubo galvanizado de 1/2"', 'UN', Decimal('16.00')),
        (199, 'Tubo galvanizado de 1"', 'UN', Decimal('1.00')),
        (200, 'Tubo galvanizado de 3/4"', 'UN', Decimal('6.00')),
        (201, 'Tubo galvanizado de 4"', 'UN', Decimal('3.00')),
        (202, 'Unión de 6"', 'UN', Decimal('6.00')),
        (203, 'Luminaria LED', 'UN', Decimal('9.00')),
        (204, 'Soporte para Pin', 'UN', Decimal('0')),
    ]

    for item_num, desc, unit, stock in NUEVOS_MATERIALES:
        mat, created = Material.objects.get_or_create(
            item=item_num,
            defaults={
                'descripcion': desc,
                'unidad': unit
            }
        )
        if not created and mat.descripcion != desc:
            mat.descripcion = desc
            mat.unidad = unit
            mat.save()

        inv, _ = Inventario.objects.get_or_create(
            material=mat,
            defaults={'cantidad': Decimal('0')}
        )
        if stock > 0 and inv.cantidad == 0:
            inv.cantidad = stock
            inv.save()
            MovimientoInventario.objects.create(
                material=mat,
                tipo_movimiento='ENTRADA',
                cantidad=stock,
                stock_anterior=Decimal('0'),
                stock_resultante=stock,
                usuario=admin_user,
                usuario_nombre="Bodega Central (Carga Inicial)",
                detalle_origen_destino="Bodega Principal (Inventario Inicial Excel)",
                observacion="Ingreso inicial de bodega desde archivo Excel INVENTARIO MATERIAL",
                fecha=timezone.now()
            )

    # 33 Materiales preexistentes con stock físico en bodega
    STOCK_EXISTENTES = [
        (21, Decimal('29.00')),
        (22, Decimal('8.00')),
        (23, Decimal('24.00')),
        (25, Decimal('20.00')),
        (28, Decimal('20.00')),
        (30, Decimal('5.00')),
        (31, Decimal('24.00')),
        (43, Decimal('200.00')),
        (46, Decimal('50.00')),
        (47, Decimal('15.00')),
        (55, Decimal('44.00')),
        (57, Decimal('11.00')),
        (58, Decimal('72.00')),
        (64, Decimal('24.00')),
        (66, Decimal('61.00')),
        (67, Decimal('6.00')),
        (68, Decimal('12.00')),
        (73, Decimal('6.00')),
        (76, Decimal('82.00')),
        (77, Decimal('40.00')),
        (78, Decimal('14.00')),
        (88, Decimal('14.00')),
        (90, Decimal('34.00')),
        (92, Decimal('61.00')),
        (102, Decimal('5.00')),
        (123, Decimal('19.00')),
        (124, Decimal('9.00')),
        (125, Decimal('10.00')),
        (126, Decimal('3.00')),
        (127, Decimal('9.00')),
        (131, Decimal('4.00')),
        (158, Decimal('16.00')),
        (712, Decimal('1.00')),
    ]

    for item_num, stock_target in STOCK_EXISTENTES:
        mat = Material.objects.filter(item=item_num).first()
        if mat:
            inv, _ = Inventario.objects.get_or_create(
                material=mat,
                defaults={'cantidad': Decimal('0')}
            )
            if inv.cantidad == 0 and stock_target > 0:
                inv.cantidad = stock_target
                inv.save()
                MovimientoInventario.objects.create(
                    material=mat,
                    tipo_movimiento='AJUSTE',
                    cantidad=stock_target,
                    stock_anterior=Decimal('0'),
                    stock_resultante=stock_target,
                    usuario=admin_user,
                    usuario_nombre="Bodega Central (Carga Inicial)",
                    detalle_origen_destino="Bodega Principal (Inventario Inicial Excel)",
                    observacion="Carga inicial de inventario físico desde Excel Hoja3",
                    fecha=timezone.now()
                )

    # Garantizar inventario en todos los materiales
    for m in Material.objects.all():
        Inventario.objects.get_or_create(material=m, defaults={'cantidad': Decimal('0')})


def revertir_materiales(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0071_empleado_dias_vacaciones_tomados_historico'),
    ]

    operations = [
        migrations.RunPython(cargar_materiales_e_inventario, revertir_materiales),
    ]
