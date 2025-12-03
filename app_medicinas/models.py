from django.db import models
from django.core.validators import MinValueValidator, MinLengthValidator, MaxValueValidator
import os

class Ubicacion(models.Model):
    id_ubicacion = models.AutoField(primary_key=True)
    desc_ubicacion = models.CharField(max_length=400, default="No indica", validators=[MinLengthValidator(2)])
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.desc_ubicacion

    class Meta:
        db_table = 'ubicaciones'


def imagen_ruta(instance, filename):
    return f'{instance.id_medicina}/{filename}'


class Presentacion_Medicamento(models.Model):
    id_presentacion_medicamento = models.AutoField(primary_key=True)
    desc_presentacion_medicamento = models.CharField(default="No indica", max_length=350, validators=[MinLengthValidator(2)])
    
    def __str__(self):
        return self.desc_presentacion_medicamento

    class Meta:
        db_table = 'presentaciones_medicamentos'


class Medicina(models.Model):
    id_medicina = models.AutoField(primary_key=True)
    imagen_medicina = models.ImageField(upload_to=imagen_ruta, null=True, blank=True)
    medicina = models.CharField(max_length=400, null=False, blank=False, default="No indica", validators=[MinLengthValidator(2)])
    presentacion = models.ForeignKey(Presentacion_Medicamento, on_delete=models.PROTECT, null=False, related_name="fk_presentacion_medicamento")

    cantidad = models.IntegerField(default=0, null=False, validators=[MaxValueValidator(100000),  MinValueValidator(0)])

    laboratorio = models.CharField(max_length=350, null=True, default="No indica", validators=[MinLengthValidator(2)])

    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.PROTECT, null=False, related_name="fk_ubicacion")

    anaquel = models.CharField(max_length=100, default="No indica", validators=[MinLengthValidator(1)])

    descripcion = models.TextField(max_length=800, null=False, blank=False)
    observaciones = models.TextField(max_length=800, null=True, blank=True)

    creador_del_registro = models.CharField(max_length=350, null=False, blank=False, default="No indica",  validators=[MinLengthValidator(2)])

    historial_edicion = models.TextField(null=False, blank=False, default="Nadie")

    fecha_registro = models.DateField(null=False, blank=False)

    def __str__(self):
        return f"{self.medicina} de {self.laboratorio}"

    class Meta:
        db_table = 'medicinas'

    def delete(self, using=None, keep_parents=False):
        if self.imagen_medicina:
            if os.path.isfile(self.imagen_medicina.path):
                os.remove(self.imagen_medicina.path)
        super().delete(using=using, keep_parents=keep_parents)
        


