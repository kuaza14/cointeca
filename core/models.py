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

    foto = models.ImageField(
        upload_to='empleados/fotos/',
        blank=True,
        null=True
    )
    nombre_completo = models.CharField(max_length=200)

    documento = models.CharField(
        max_length=20,
        unique=True,
        
    )

    ciudad_expedicion = models.CharField(
        max_length=100,
        blank=True
    )

    fecha_nacimiento = models.DateField(
        max_length=10,
        blank=True,
        null=True
    )

    nacionalidad = models.CharField(
        max_length=50,
        default='Colombiano'
    )

    direccion = models.TextField()

    ciudad_residencia = models.CharField(
        max_length=100,
        blank=True
    )

    barrio = models.CharField(
        max_length=100,
        blank=True
    )

    estrato = models.PositiveSmallIntegerField(
        null=True,
        blank=True
    )

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
    fecha_ingreso = models.DateField(
        null=True,
        blank=True
    )
    fecha_finalizacion = models.DateField(blank=True, null=True)

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

    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.CASCADE,
        related_name="dotaciones"
    )

    fecha_entrega = models.DateField()

    observacion = models.TextField(
        blank=True,
        null=True
    )

    class Meta:
        ordering = ["-fecha_entrega"]

    def __str__(self):
        return f"{self.empleado.nombre_completo} - {self.fecha_entrega}"

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

class SolicitudVacaciones(models.Model):

    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.CASCADE
    )

    fecha_solicitud = models.DateField()

    periodo_desde = models.DateField()
    periodo_hasta = models.DateField()

    dias_solicitados = models.IntegerField()

    vacaciones_desde = models.DateField()
    vacaciones_hasta = models.DateField()

    dias_disponibles = models.IntegerField(default=15)

    nombre_rrhh = models.CharField(max_length=200)

    jefe_inmediato = models.CharField(max_length=200)

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.empleado.nombre_completo} - Vacaciones"

class Vacacion(models.Model):

    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.CASCADE
    )

    periodo = models.CharField(
        max_length=20
    )

    fecha_inicio = models.DateField()

    fecha_fin = models.DateField()

    dias_tomados = models.IntegerField()

    dias_pendientes = models.IntegerField()

    fecha_regreso = models.DateField(
        null=True,
        blank=True
    )

    observaciones = models.TextField(
        blank=True,
        null=True
    )

    fecha_registro = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"{self.empleado.nombre_completo} - {self.periodo}"
        )

class Descargo(models.Model):

    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.CASCADE
    )

    representante_rrhh = models.CharField(
        max_length=150,
        default='Gestión RRHH'
    )

    testigo = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    fecha_hechos = models.DateField()

    descripcion_falta = models.TextField()

    hora_inicio = models.TimeField()

    hora_cierre = models.TimeField(
        blank=True,
        null=True
    )

    observaciones_finales = models.TextField(
        blank=True,
        null=True
    )

    fecha_registro = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.empleado.nombre_completo

class CitacionDescargo(models.Model):

    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.CASCADE
    )

    fecha_diligencia = models.DateField()

    hora_diligencia = models.TimeField()

    lugar_diligencia = models.CharField(
        max_length=150,
        default='Oficina de RRHH'
    )

    descripcion_hechos = models.TextField()

    clausula_contrato = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    articulo_reglamento = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    norma_cst = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    fecha_registro = models.DateTimeField(
        auto_now_add=True
    )

class RetiroCesantias(models.Model):

    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.CASCADE
    )

    tipo_retiro = models.CharField(
        max_length=20
    )

    fecha_solicitud = models.DateField()

    fondo_cesantias = models.CharField(
        max_length=100,
        default='Protección'
    )

    valor_retiro = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )

    direccion_vivienda = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    descripcion_vivienda = models.TextField(
        blank=True,
        null=True
    )

    institucion_educativa = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    programa_estudio = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    beneficiario = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    fecha_retiro_definitivo = models.DateField(
        blank=True,
        null=True
    )

    observaciones = models.TextField(
        blank=True,
        null=True
    )

    fecha_registro = models.DateTimeField(
        auto_now_add=True
    )

class InduccionCapacitacion(models.Model):

    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.CASCADE
    )

    fecha = models.DateField()

    TIPO_EVENTO = [
        ('INDUCCION', 'Inducción'),
        ('REINDUCCION', 'Reinducción'),
        ('CAPACITACION', 'Capacitación específica'),
    ]

    tipo_evento = models.CharField(
        max_length=20,
        choices=TIPO_EVENTO
    )

    # Sección 3 del formato (solo si aplica)
    tema_capacitacion = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    facilitador = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    duracion_horas = models.PositiveIntegerField(
        blank=True,
        null=True
    )

    fecha_registro = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return (
            f'{self.empleado.nombre_completo} - '
            f'{self.get_tipo_evento_display()}'
        )

class CompromisoPagoDano(models.Model):

    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.CASCADE
    )

    numero_acta = models.CharField(
        max_length=20
    )

    valor_descuento = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    descripcion_dano = models.TextField()

    fecha_evento = models.DateField()

    fecha_registro = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return (
            f'{self.empleado.nombre_completo} - '
            f'Acta {self.numero_acta}'
        )

class RetiroEmpleado(models.Model):

    empleado = models.OneToOneField(
        Empleado,
        on_delete=models.CASCADE
    )

    fecha_retiro = models.DateField()

    motivo = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    observaciones = models.TextField(
        blank=True,
        null=True
    )

    fecha_registro = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.empleado.nombre_completo

class SuspensionContrato(models.Model):

    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.CASCADE
    )

    fecha_inicio = models.DateField()

    fecha_fin = models.DateField()

    motivo = models.TextField(blank=True)

    fecha_registro = models.DateTimeField(auto_now_add=True)

class ContratoAprendizaje(models.Model):

    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.CASCADE
    )

    institucion = models.CharField(
        max_length=200
    )

    nit_institucion = models.CharField(
        max_length=50,
        blank=True
    )

    centro_formacion = models.CharField(
        max_length=200,
        blank=True
    )

    especialidad = models.CharField(max_length=200)

    numero_grupo = models.CharField(max_length=50)

    modalidad = models.CharField(
        max_length=30
    )

    fecha_inicio = models.DateField()

    fecha_fin = models.DateField()

    fecha_inicio_lectiva = models.DateField()

    fecha_fin_lectiva = models.DateField()

    fecha_inicio_practica = models.DateField()

    fecha_fin_practica = models.DateField()

    porcentaje_apoyo = models.IntegerField(
        default=100
    )

class SuspensionDisciplinaria(models.Model):
    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.CASCADE,
        related_name='suspensiones_disciplinarias'
    )

    # Motivo de la suspensión
    motivo_suspension = models.TextField()

    # Fecha en que ocurrió la falta
    fecha_falta = models.DateField()

    # Uno o varios artículos, incluyendo su descripción
    articulos_infringidos = models.TextField()

    # Periodo de suspensión
    fecha_inicio_suspension = models.DateField()
    fecha_fin_suspension = models.DateField()

    # Fecha en que debe regresar a trabajar
    fecha_reincorporacion = models.DateField()

    # Opcionales, porque pueden variar según el caso
    responsabilidad_pecuniaria = models.TextField(
        blank=True,
        null=True
    )

    consecuencia_reincidencia = models.TextField(
        blank=True,
        null=True
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.empleado.nombre_completo} - {self.fecha_falta}"

####################################################
#                  INGENIERÍA
####################################################

class Proyecto(models.Model):
    class Tipos(models.TextChoices):
        BT = "BT", "Baja Tensión"
        AP = "AP", "Alumbrado Público"
        MT = "MT", "Media Tensión"

    class Estados(models.TextChoices):
        PLANEACION = "Planeación", "Planeación"
        EN_EJECUCION = "En ejecución", "En ejecución"
        FINALIZADO = "Finalizado", "Finalizado"
        CANCELADO = "Cancelado", "Cancelado"

    numero_emcali = models.CharField(max_length=50, unique=True, verbose_name="Número Proyecto")
    tipo = models.CharField(max_length=2, choices=Tipos.choices)
    estado = models.CharField(max_length=30, choices=Estados.choices, default=Estados.PLANEACION)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Proyecto"
        verbose_name_plural = "Proyectos"

    def __str__(self):
        return self.numero_emcali

class Apoyo(models.Model):
    class Estados(models.TextChoices):
        PENDIENTE = "Pendiente", "Pendiente"
        EN_EJECUCION = "En ejecución", "En ejecución"
        FINALIZADO = "Finalizado", "Finalizado"

    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name="apoyos", blank=True, null=True)
    nombre_quien_ejecuta = models.CharField(max_length=100, blank=True)
    nodo = models.CharField(max_length=100, blank=True, null=True)
    numero_apoyo = models.PositiveIntegerField(null=True, blank=True)
    observacion = models.TextField(blank=True, default="")
    estado = models.CharField(max_length=20, choices=Estados.choices, default=Estados.PENDIENTE)

    class Meta:
        verbose_name = "Apoyo"
        verbose_name_plural = "Apoyos"
        ordering = ["numero_apoyo"]

    def __str__(self):
        if self.nodo:
            return f"{self.proyecto.numero_emcali if self.proyecto else 'Sin Proyecto'} - Nodo {self.nodo}"
        return f"{self.proyecto.numero_emcali if self.proyecto else 'Sin Proyecto'} - Apoyo {self.numero_apoyo}"

class Material(models.Model):
    item = models.IntegerField(unique=True)
    descripcion = models.CharField(max_length=250)
    unidad = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        verbose_name = "Material"
        verbose_name_plural = "Materiales"
        ordering = ["item"]

    def __str__(self):
        return f"{self.item} - {self.descripcion}"

class Inventario(models.Model):

    material = models.OneToOneField(
        Material,
        on_delete=models.CASCADE,
        related_name="inventario",
        null=True,
        blank=True
    )

    cantidad = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    def __str__(self):
        return f"{self.material.descripcion} - {self.cantidad}"

class ApoyoMaterial(models.Model):
    apoyo = models.ForeignKey(Apoyo, on_delete=models.CASCADE, related_name="materiales")
    material = models.ForeignKey(Material, on_delete=models.PROTECT, related_name="apoyos")
    cantidad_requerida = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Material por Apoyo"
        verbose_name_plural = "Materiales por Apoyo"
        unique_together = ("apoyo", "material")

    def __str__(self):
        return f"{self.material.descripcion} - Apoyo {self.apoyo.numero_apoyo}"

class Presupuesto(models.Model):

    proyecto = models.OneToOneField(
        Proyecto,
        on_delete=models.CASCADE,
        related_name="presupuesto"
    )

    valor_materiales = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    valor_mano_obra = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    otros_costos = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    valor_total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    fecha = models.DateField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = "Presupuesto"
        verbose_name_plural = "Presupuestos"

    def __str__(self):
        return f"Presupuesto {self.proyecto.numero_emcali}"


####################################################
#             LOGÍSTICA - MATERIALES Y PROYECTO
####################################################

class EntradaMaterialProyecto(models.Model):
    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.CASCADE,
        related_name="entradas_material"
    )
    fecha = models.DateField()
    proveedor = models.CharField(
        max_length=150,
        blank=True,
        default="",
        verbose_name="Proveedor"
    )
    numero_remision = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="N° Remisión / Factura"
    )
    recibido_por = models.CharField(
        max_length=150,
        blank=True,
        default="",
        verbose_name="Recibido por"
    )
    observaciones = models.TextField(
        blank=True,
        default=""
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = "Entrada de Material a Proyecto"
        verbose_name_plural = "Entradas de Material a Proyectos"
        ordering = ["-fecha", "-id"]

    def __str__(self):
        return f"Entrada {self.proyecto.numero_emcali} - {self.fecha} ({self.numero_remision})"


class DetalleEntradaMaterial(models.Model):
    entrada = models.ForeignKey(
        EntradaMaterialProyecto,
        on_delete=models.CASCADE,
        related_name="detalles"
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        related_name="entradas_proyecto"
    )
    cantidad = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    class Meta:
        verbose_name = "Detalle Entrada Material"
        verbose_name_plural = "Detalles Entrada Material"

    def __str__(self):
        return f"{self.material.descripcion}: {self.cantidad}"


class ConsumoMaterialProyecto(models.Model):
    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.CASCADE,
        related_name="consumos_material"
    )
    fecha_reporte = models.DateField(
        verbose_name="Fecha Reporte"
    )
    supervisor = models.CharField(
        max_length=150,
        blank=True,
        default="",
        verbose_name="Supervisor / Quien entrega"
    )
    numero_planilla = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="N° Planilla / Reporte"
    )
    observaciones = models.TextField(
        blank=True,
        default=""
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = "Consumo de Material en Obra"
        verbose_name_plural = "Consumos de Material en Obra"
        ordering = ["-fecha_reporte", "-id"]

    def __str__(self):
        return f"Consumo {self.proyecto.numero_emcali} - {self.fecha_reporte} ({self.supervisor})"


class DetalleConsumoMaterial(models.Model):
    consumo = models.ForeignKey(
        ConsumoMaterialProyecto,
        on_delete=models.CASCADE,
        related_name="detalles"
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        related_name="consumos_proyecto"
    )
    cantidad = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Cantidad Utilizada"
    )

    class Meta:
        verbose_name = "Detalle Consumo Material"
        verbose_name_plural = "Detalles Consumo Material"

    def __str__(self):
        return f"{self.material.descripcion}: {self.cantidad}"
