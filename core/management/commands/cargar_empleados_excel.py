import os
import re
import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Empleado, SaludEmpleado


class Command(BaseCommand):
    help = "Carga colaboradores desde el archivo Excel de Cointeca omitiendo los ya registrados en el sistema."

    def add_arguments(self, parser):
        parser.add_argument(
            '--archivo',
            type=str,
            default='/app/temp_trabajadores.xlsx',
            help='Ruta al archivo Excel de trabajadores'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular la carga sin guardar cambios en la base de datos'
        )

    def parse_fecha(self, val):
        if not val:
            return None
        if isinstance(val, datetime.datetime):
            return val.date()
        if isinstance(val, datetime.date):
            return val
        if isinstance(val, str):
            val_clean = val.strip()
            for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%y'):
                try:
                    return datetime.datetime.strptime(val_clean, fmt).date()
                except ValueError:
                    continue
        return None

    def handle(self, *args, **options):
        import openpyxl

        excel_path = options['archivo']
        dry_run = options['dry_run']

        if not os.path.exists(excel_path):
            alt_path = os.path.join(os.getcwd(), 'temp_trabajadores.xlsx')
            if os.path.exists(alt_path):
                excel_path = alt_path
            else:
                self.stderr.write(self.style.ERROR(f"No se encontró el archivo Excel en {excel_path}"))
                return

        self.stdout.write(f"Leyendo trabajadores desde: {excel_path}...")
        wb = openpyxl.load_workbook(excel_path, read_only=True, data_only=True)
        if 'ACTIVOS' not in wb.sheetnames:
            self.stderr.write(self.style.ERROR("La hoja 'ACTIVOS' no existe en el archivo Excel."))
            wb.close()
            return

        ws_activos = wb['ACTIVOS']

        # Extraer documentos y nombres de empleados existentes en DB
        empleados_db = Empleado.objects.all()
        docs_existentes = set()
        nombres_palabras_db = []

        for e in empleados_db:
            doc_clean = re.sub(r'\D', '', str(e.documento or ''))
            if doc_clean:
                docs_existentes.add(doc_clean)
            palabras = set(re.findall(r'\w+', (e.nombre_completo or '').upper()))
            if palabras:
                nombres_palabras_db.append(palabras)

        self.stdout.write(f"Empleados activos encontrados en la base de datos: {len(empleados_db)}")

        # Salarios por defecto según cargo
        salarios_base = {
            'LINIERO': Decimal('2650000.00'),
            'SUPERVISOR': Decimal('3323000.00'),
            'AUXILIAR': Decimal('1600000.00'),
            'AUX.CONTABLE': Decimal('1800000.00'),
            'CONDUCTOR': Decimal('2000000.00'),
            'INGENIERO': Decimal('3500000.00'),
            'PROFECIONAL SST': Decimal('3400000.00'),
            'PROFESIONAL SST': Decimal('3400000.00'),
        }

        # Procesar filas de ACTIVOS
        creados = 0
        omitidos = 0

        # Para Cristiam Camilo Ospina Franco (si su documento viene vacío en ACTIVOS, usar el de histórico)
        doc_respaldo_ospina = "1144109447"

        with transaction.atomic():
            for i, r in enumerate(ws_activos.iter_rows(values_only=True)):
                if i < 2:
                    continue
                nombre_raw = r[1]
                if not nombre_raw:
                    continue

                nombre = str(nombre_raw).strip()
                if nombre.upper() in ['APRENDIZ SENA', 'EDSON YILMAR CASTAÑO']:
                    continue

                doc_raw = str(r[2] or '').strip()
                doc_clean = re.sub(r'\D', '', doc_raw)

                # Si es Ospina Franco y no tiene doc en la fila
                if not doc_clean and 'OSPINA' in nombre.upper() and 'CRISTHIAN' in nombre.upper():
                    doc_clean = doc_respaldo_ospina

                if not doc_clean:
                    self.stdout.write(self.style.WARNING(f"Fila {i}: Omitido {nombre} por falta de documento."))
                    omitidos += 1
                    continue

                # Validar si ya existe por documento o por nombre similar (conjunto de palabras)
                palabras_actual = set(re.findall(r'\w+', nombre.upper()))
                coincide_nombre = False
                for p_db in nombres_palabras_db:
                    inter = palabras_actual.intersection(p_db)
                    # Si coinciden al menos 3 palabras o más del 70% del nombre
                    if len(inter) >= 3 or (len(palabras_actual) >= 2 and len(inter) >= len(palabras_actual) * 0.75):
                        coincide_nombre = True
                        break

                if doc_clean in docs_existentes or coincide_nombre:
                    self.stdout.write(self.style.NOTICE(f"Fila {i}: Omitido {nombre} (C.C. {doc_clean}) ya está registrado en el sistema."))
                    omitidos += 1
                    continue

                # Extraer campos
                cargo_raw = str(r[20] if len(r) > 20 and r[20] else 'AUXILIAR').strip().upper()
                cargo = cargo_raw if cargo_raw else 'AUXILIAR'
                salario = salarios_base.get(cargo, Decimal('1600000.00'))

                dir_res = str(r[5] if len(r) > 5 and r[5] else 'No registrada').strip()
                ciudad_exp = str(r[4] if len(r) > 4 and r[4] else '').strip()
                fecha_nac = self.parse_fecha(r[6] if len(r) > 6 else None)
                fecha_ing = self.parse_fecha(r[22] if len(r) > 22 else None)
                if not fecha_ing:
                    fecha_ing = datetime.date(2024, 1, 15)

                grupo_sang = str(r[9] if len(r) > 9 and r[9] else 'O+').strip()
                eps = str(r[10] if len(r) > 10 and r[10] else 'SURA').strip()
                afp = str(r[11] if len(r) > 11 and r[11] else 'PORVENIR').strip()
                cesantias = str(r[12] if len(r) > 12 and r[12] else afp).strip()
                if not cesantias:
                    cesantias = afp

                tel_raw = str(r[18] if len(r) > 18 and r[18] else '').strip()
                tel_clean = re.sub(r'[^\d]', '', tel_raw)
                telefono = tel_clean if tel_clean else '3000000000'

                mail_raw = str(r[19] if len(r) > 19 and r[19] else '').strip()
                correo = mail_raw if '@' in mail_raw else f"{doc_clean}@cointeca.com"

                # Área y nivel académico
                if 'CONTABLE' in cargo:
                    area = 'ADMINISTRATIVA'
                    nivel_acad = 'Técnico'
                elif 'INGENIERO' in cargo or 'SST' in cargo:
                    area = 'ADMINISTRATIVA'
                    nivel_acad = 'Profesional'
                elif 'CONDUCTOR' in cargo:
                    area = 'OPERATIVO'
                    nivel_acad = 'Bachiller'
                else:
                    area = 'OPERATIVO'
                    nivel_acad = 'Bachiller'

                jefe = 'GERENTE' if area == 'ADMINISTRATIVA' else 'SUPERVISOR'

                if not dry_run:
                    empleado = Empleado.objects.create(
                        foto=None,
                        nombre_completo=nombre,
                        documento=doc_clean,
                        ciudad_expedicion=ciudad_exp,
                        fecha_nacimiento=fecha_nac,
                        nacionalidad='Colombiano',
                        direccion=dir_res,
                        ciudad_residencia='Cali',
                        barrio='',
                        estrato=2,
                        telefono=telefono,
                        correo=correo,
                        contacto_emergencia='',
                        telefono_emergencia='',
                        parentesco_emergencia='',
                        cargo=cargo,
                        area=area,
                        nivel_academico=nivel_acad,
                        profesion=cargo,
                        habilidades='',
                        idiomas='Español',
                        fecha_ingreso=fecha_ing,
                        fecha_finalizacion=None,
                        tipo_contrato='fijo',
                        salario=salario,
                        jornada='diurna',
                        jefe=jefe,
                        estado='activo'
                    )

                    SaludEmpleado.objects.create(
                        empleado=empleado,
                        grupo_sanguineo=grupo_sang[:5] if grupo_sang else 'O+',
                        eps=eps,
                        pension=afp,
                        cesantias=cesantias,
                        arl='AXA COLPATRIA',
                        alergias='Ninguna',
                        contacto_emergencia='',
                        telefono_emergencia=''
                    )

                    # Registrar en el conjunto de existentes para evitar duplicados internos
                    docs_existentes.add(doc_clean)
                    nombres_palabras_db.append(palabras_actual)

                creados += 1
                self.stdout.write(self.style.SUCCESS(f"✅ [{'SIMULADO' if dry_run else 'REGISTRADO'}] {nombre} | C.C. {doc_clean} | Cargo: {cargo} | EPS: {eps} | AFP: {afp}"))

            if dry_run:
                self.stdout.write(self.style.WARNING(f"\n[MODO SIMULACIÓN] Se habrían registrado {creados} colaboradores. {omitidos} omitidos."))
            else:
                self.stdout.write(self.style.SUCCESS(f"\n¡Éxito! Se registraron {creados} nuevos colaboradores activos. {omitidos} fueron omitidos por ya existir o no tener documento."))

        wb.close()
