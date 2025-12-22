from django.db import models
from django.core.validators import MinValueValidator, MinLengthValidator, MaxValueValidator
from django.utils import timezone
import os
from datetime import timedelta
from datetime import date, datetime

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


class Medicina_Contador_Caducidad(models.Manager):  
    def caducados_confirmados(self):
        return self.filter(caducado=True).count()
    
    def proximos_a_vencer(self):
        desde = timezone.now().date()
        hasta = desde + timedelta(days=30)
        return self.filter(
            caducado__isnull=True,
            caducado=False,
            fecha_caducidad__isnull=False,
            fecha_caducidad__range=[desde, hasta]
        ).count()
    
    def dias_para_vencer(self, medicina_id):
        med = self.get(id=medicina_id)
        if med.fecha_caducidad:
            return (med.fecha_caducidad - timezone.now().date()).days
        return None


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

    """
        Campos nuevos, no permitir nulo y en blanco despues de que se lleven
        todos los registros oficiales.
    """
    fecha_caducidad = models.DateField(null=True, blank=True, default=None)
    caducado = models.BooleanField(default=False,  blank=True, null=True)
    objects = Medicina_Contador_Caducidad()

    class Meta:
        db_table = 'medicinas'
        indexes = [
            models.Index(fields=['caducado', 'fecha_caducidad'])
        ]

    def __str__(self):
        return f"{self.medicina} de {self.laboratorio}"
    
    def clean(self):
        errores_validacion = {}

        if self.medicina.isdigit():
            errores_validacion["error_campo_medicina"] = "El nombre de un medicamento no puede ser totalmente numerico"

        if len(self.medicina) > 400 or len(self.medicina) < 2:
            errores_validacion["error_campo_medicina"] = "Minimo 2 caracteres, maximo 400"
        
        if self.cantidad < 0 or self.cantidad > 100000:
            errores_validacion["error_campo_cantidad"] = "La cantidad introducida no es valida, debe ser mayor 0 o menor a 100000"
        
        if isinstance(self.cantidad, float) == True:
            errores_validacion["error_campo_cantidad"] = "La cantidad no debe ser un numero decimal."
        
        if len(self.laboratorio) < 2 or len(self.laboratorio) > 350:
            errores_validacion["error_campo_laboratorio"] = "El nombre del laboratorio debe tener minimo 2 caracteres y maximo 350"
        
        if len(self.anaquel) < 1 or len(self.anaquel) > 100:
            errores_validacion["error_campo_anaquel"] = "El anaquel debe ser maximo 100 caracteres y minimo 1"
        
        if not isinstance(self.fecha_caducidad, (date, datetime)):
            errores_validacion["error_campo_fecha_caducidad"] = "Fecha de caducidad no valida"

    def delete(self, using=None, keep_parents=False):
        if self.imagen_medicina:
            if os.path.isfile(self.imagen_medicina.path):
                os.remove(self.imagen_medicina.path)
        super().delete(using=using, keep_parents=keep_parents)


    def caducir(self):
        hoy = timezone.now().date()
        if self.fecha_caducidad and self.fecha_caducidad <= hoy:
            self.caducado = True
            self.save(update_fields=['caducado'])
        else:
            self.caducado = False
            self.save(update_fields=['caducado'])

    @property
    def es_caducado(self):
        return bool(self.fecha_caducidad and self.fecha_caducidad <= timezone.now().date())
    

    

        


