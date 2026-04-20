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