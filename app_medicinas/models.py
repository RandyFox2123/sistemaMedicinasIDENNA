from django.db import models
from django.core.validators import MinValueValidator, MinLengthValidator, MaxValueValidator
import os


class Almacen(models.Model):
    id_almacen = models.AutoField(primary_key=True)
    desc_almacen = models.CharField(max_length=400, default="?")
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.desc_almacen

    class Meta:
        db_table = 'almacenes'


def imagen_ruta(instance, filename):
    return f'{instance.id_medicina}/{filename}'



class Medida(models.Model):
    id_medida = models.AutoField(primary_key=True)
    desc_medida = models.CharField(default="?", max_length=150, validators=[MinLengthValidator(2)])
    
    def __str__(self):
        return self.desc_medida

    class Meta:
        db_table = 'medidas'


class Medicina(models.Model):
    id_medicina = models.AutoField(primary_key=True)
    imagen_medicina = models.ImageField(upload_to=imagen_ruta, null=True, blank=True)
    desc_medicina= models.CharField(max_length=400, default="?")
    cantidad = models.DecimalField(default=0.0, max_digits=10, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(50000)])
    medida_medicina = models.ForeignKey(Medida, on_delete=models.PROTECT, null=False, related_name="fk_medida")
    almacen_perteneciente = models.ForeignKey(Almacen, on_delete=models.PROTECT, related_name="fk_medicinas")
    

    def __str__(self):
        return self.desc_medicina

    class Meta:
        db_table = 'medicinas'

    def delete(self, using=None, keep_parents=False):
        if self.imagen_medicina:
            if os.path.isfile(self.imagen_medicina.path):
                os.remove(self.imagen_medicina.path)
        super().delete(using=using, keep_parents=keep_parents)
        
