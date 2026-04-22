from django.db import models
from django.db.models import Sum


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