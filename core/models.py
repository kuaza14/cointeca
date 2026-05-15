from django.db import models



class CajaMenor(models.Model):
    fecha_tramite = models.DateField()
    fecha_cierre = models.DateField(null=True, blank=True)

    valor_inicial = models.DecimalField(max_digits=12, decimal_places=2)
    total_gastado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valor_restante = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def calcular_totales(self):
        total = self.movimientocajamenor_set.aggregate(
            total=Sum('valor')
        )['total'] or 0

        self.total_gastado = total
        self.valor_restante = self.valor_inicial - total
        self.save()

    def __str__(self):
        return f"Caja {self.id} - {self.fecha_tramite}"

class MovimientoCajaMenor(models.Model):
    caja = models.ForeignKey(CajaMenor, on_delete=models.CASCADE)

    fecha = models.DateField()
    numero_factura = models.CharField(max_length=50)
    nit = models.CharField(max_length=50)

    pagado_a = models.CharField(max_length=150)
    concepto = models.TextField()

    valor = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.caja.calcular_totales()

    def __str__(self):
        return f"{self.numero_factura} - {self.valor}"

class ActaJuntaDirectiva(models.Model):

    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('aprobada', 'Aprobada'),
        ('anulada', 'Anulada'),
    ]

    numero_acta = models.CharField(max_length=20, unique=True)
    nombre_entidad = models.CharField(max_length=200)
    nit = models.CharField(max_length=20)

    fecha = models.DateField()
    hora_inicio = models.TimeField()
    lugar = models.CharField(max_length=200)

    presidente = models.CharField(max_length=150)
    secretario = models.CharField(max_length=150)

    orden_del_dia = models.TextField()
    desarrollo = models.TextField()
    proposiciones = models.TextField(blank=True, null=True)

    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='borrador')

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Acta {self.numero_acta} - {self.fecha}"

class IndicadorEstrategico(models.Model):

    PERSPECTIVA_CHOICES = [
        ('financiera', 'Financiera'),
        ('comercial', 'Comercial'),
        ('operativa', 'Operativa'),
        ('cliente', 'Cliente'),
        ('aprendizaje', 'Aprendizaje'),
    ]

    FRECUENCIA_CHOICES = [
        ('mensual', 'Mensual'),
        ('trimestral', 'Trimestral'),
        ('semestral', 'Semestral'),
        ('anual', 'Anual'),
        ('por_proyecto', 'Por Proyecto'),
    ]

    perspectiva = models.CharField(max_length=20, choices=PERSPECTIVA_CHOICES)
    nombre = models.CharField(max_length=200)
    definicion = models.TextField()
    meta_anual = models.CharField(max_length=100)
    frecuencia = models.CharField(max_length=20, choices=FRECUENCIA_CHOICES)

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.perspectiva} - {self.nombre}"


class SeguimientoIndicador(models.Model):
    indicador = models.ForeignKey(IndicadorEstrategico, on_delete=models.CASCADE)
    fecha = models.DateField()
    valor_obtenido = models.CharField(max_length=100)
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.indicador.nombre} - {self.fecha}"

class ProyectoFacturacion(models.Model):
    nombre = models.CharField(max_length=200)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class SeguimientoFacturacion(models.Model):
    MES_CHOICES = [
        ('enero', 'Enero'),
        ('febrero', 'Febrero'),
        ('marzo', 'Marzo'),
        ('abril', 'Abril'),
        ('mayo', 'Mayo'),
        ('junio', 'Junio'),
        ('julio', 'Julio'),
        ('agosto', 'Agosto'),
        ('septiembre', 'Septiembre'),
        ('octubre', 'Octubre'),
        ('noviembre', 'Noviembre'),
        ('diciembre', 'Diciembre'),
    ]

    mes = models.CharField(max_length=20, choices=MES_CHOICES)
    anio = models.IntegerField(default=2026)
    meta_facturacion = models.DecimalField(max_digits=15, decimal_places=2)
    facturacion_real = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    proyecto = models.ForeignKey(ProyectoFacturacion, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('mes', 'anio', 'proyecto')

    @property
    def porcentaje_cumplimiento(self):
        if self.meta_facturacion > 0:
            return round((self.facturacion_real / self.meta_facturacion) * 100, 1)
        return 0

    def __str__(self):
        return f"{self.proyecto.nombre} - {self.mes} {self.anio}"

class Empleado(models.Model):

    # =========================================================
    # 1. INFORMACIÓN PERSONAL
    # =========================================================
    nombre_completo = models.CharField(max_length=200)

    documento = models.CharField(
        max_length=20,
        unique=True,
        
    )

    ciudad_expedicion = models.CharField(
        max_length=100,
        blank=True
    )

    fecha_nacimiento = models.DateField()

    nacionalidad = models.CharField(
        max_length=50,
        default='Colombiano'
    )

    direccion = models.TextField()

    telefono = models.CharField(max_length=20)

    correo = models.EmailField()

    estado_civil = models.CharField(
        max_length=50,
        blank=True
    )

    # =========================================================
    # 2. PERFIL PROFESIONAL
    # =========================================================
    cargo = models.CharField(max_length=100)

    area = models.CharField(max_length=100)

    nivel_academico = models.CharField(max_length=100)

    profesion = models.CharField(
        max_length=100,
        blank=True
    )

    habilidades = models.TextField(blank=True)

    idiomas = models.CharField(
        max_length=100,
        default='Español'
    )

    # =========================================================
    # 3. INFORMACIÓN CONTRACTUAL
    # =========================================================
    fecha_ingreso = models.DateField()

    TIPO_CONTRATO = [
        ('fijo', 'Fijo'),
        ('indefinido', 'Indefinido'),
        ('obra', 'Obra o labor'),
        ('aprendizaje', 'Aprendizaje'),
    ]

    tipo_contrato = models.CharField(
        max_length=20,
        choices=TIPO_CONTRATO
    )

    salario = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    JORNADA = [
        ('diurna', 'Diurna'),
        ('nocturna', 'Nocturna'),
        ('mixta', 'Mixta'),
    ]

    jornada = models.CharField(
        max_length=20,
        choices=JORNADA
    )

    jefe = models.CharField(max_length=150)

    estado = models.CharField(
        max_length=20,
        default='activo'
    )

    # =========================================================
    # 4. CONTACTO DE EMERGENCIA
    # =========================================================
    contacto_emergencia = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    telefono_emergencia = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    parentesco_emergencia = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    # =========================================================
    # 5. SEGURIDAD SOCIAL
    # =========================================================
    grupo_sanguineo = models.CharField(
        max_length=10,
        blank=True,
        null=True
    )

    eps = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    arl = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    afp = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    cesantias = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    alergias = models.TextField(blank=True)

    # 6. INFORMACIÓN ADICIONAL
    observaciones = models.TextField(blank=True)

    fecha_retiro = models.DateField(
        null=True,
        blank=True
    )

    motivo_retiro = models.TextField(blank=True)

    def __str__(self):
        return f"{self.nombre_completo} - {self.documento}"

class SaludEmpleado(models.Model):
    empleado = models.OneToOneField(Empleado, on_delete=models.CASCADE)

    grupo_sanguineo = models.CharField(max_length=5)
    eps = models.CharField(max_length=100)
    pension = models.CharField(max_length=100)
    cesantias = models.CharField(max_length=100)
    arl = models.CharField(max_length=100)

    alergias = models.TextField(blank=True)

    contacto_emergencia = models.CharField(max_length=150)
    telefono_emergencia = models.CharField(max_length=20)

class DotacionEmpleado(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)

    elemento = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=200)
    fecha_entrega = models.DateField()

class AsignacionEquipo(models.Model):

    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.CASCADE
    )

    equipo_inventario = models.ForeignKey(
        'InventarioEquipo',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    fecha_entrega = models.DateField()

    observaciones = models.TextField(
        blank=True,
        null=True
    )

class ActaEntregaEquipo(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    fecha = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Acta Equipos - {self.empleado.nombre_completo} - {self.fecha}"

class InventarioEquipo(models.Model):

    equipo = models.CharField(max_length=100)
    referencia = models.CharField(max_length=100)
    serial = models.CharField(max_length=100)

    ESTADOS = [
        ('disponible', 'Disponible'),
        ('asignado', 'Asignado'),
        ('mantenimiento', 'Mantenimiento'),
    ]

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='disponible'
    )

    fecha_compra = models.DateField()
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.equipo} - {self.serial}"

class Contrato(models.Model):

    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.CASCADE
    )

    tipo_contrato = models.CharField(max_length=100)

    fecha_inicio = models.DateField()

    fecha_fin = models.DateField(
        null=True,
        blank=True
    )

    salario = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    cargo = models.CharField(max_length=100)

    estado = models.CharField(
        max_length=50,
        default='Activo'
    )

    observaciones = models.TextField(blank=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.empleado.nombre_completo} - {self.tipo_contrato}"

class DocumentoEmpleado(models.Model):
    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.CASCADE
    )

    nombre = models.CharField(max_length=200)

    archivo = models.FileField(
        upload_to='documentos_rrhh/'
    )

    fecha = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.nombre
