from django.db import models
from django.core.validators import MinValueValidator, MinLengthValidator, MaxValueValidator
from django.utils import timezone
import os
from datetime import timedelta
from datetime import date, datetime
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
import uuid

def fotos_medicinas_upload_path(instance, filename):
    if instance.id_medicina:
        extension = os.path.splitext(filename)[1]
        return f"fotos_medicinas/MED{instance.id_medicina}{extension}"
    else:  
        return f"fotos_medicinas/temp{os.path.splitext(filename)[1]}"


class Ubicacion(models.Model):
    id_ubicacion = models.AutoField(primary_key=True)
    desc_ubicacion = models.CharField(max_length=400, default="No indica", validators=[MinLengthValidator(2)])
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.desc_ubicacion

    class Meta:
        db_table = 'ubicaciones'


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

    imagen_medicina = models.ImageField(upload_to=fotos_medicinas_upload_path, null=True, blank=True)

    medicina = models.CharField(max_length=400, null=False, blank=False, default="No indica", validators=[MinLengthValidator(2)])

    presentacion = models.ForeignKey(Presentacion_Medicamento, on_delete=models.PROTECT, null=False, related_name="fk_presentacion_medicamento")

    cantidad = models.IntegerField(default=0, null=False, validators=[MaxValueValidator(100000), MinValueValidator(0)])

    laboratorio = models.CharField(max_length=350, null=True, default="No indica", validators=[MinLengthValidator(2)])

    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.PROTECT, null=False, related_name="fk_ubicacion")

    anaquel = models.CharField(max_length=100, default="No indica", validators=[MinLengthValidator(1)])

    descripcion = models.TextField(max_length=800, null=False, blank=False)
    observaciones = models.TextField(max_length=800, null=True, blank=True)

    creador_del_registro = models.CharField(max_length=350, null=False, blank=False, default="No indica", validators=[MinLengthValidator(2)])

    historial_edicion = models.TextField(null=False, blank=False, default="Nadie")

    fecha_registro = models.DateField(null=False, blank=False, default=timezone.now().date)

    fecha_caducidad = models.DateField(null=True, blank=True, default=None)
    caducado = models.BooleanField(default=False, blank=True, null=True)
    objects = Medicina_Contador_Caducidad()

    class Meta:
        db_table = 'medicinas'
        indexes = [
            models.Index(fields=['caducado', 'fecha_caducidad'])
        ]

    def __str__(self):
        return f"{self.medicina} de {self.laboratorio}"

    def clean(self):
        if self.medicina.isdigit():
            raise ValidationError({
                'medicina': _('El nombre no puede ser totalmente numérico.')
            })

        if len(self.medicina) > 400 or len(self.medicina) < 2:
            raise ValidationError({
                'medicina': _('Mínimo 2, máximo 400 caracteres.')
            })

        if self.cantidad < 0 or self.cantidad > 100000:
            raise ValidationError({
                'cantidad': _('Debe ser entre 0 y 100000.')
            })

        if not isinstance(self.cantidad, int):
            raise ValidationError({
                'cantidad': _('Debe ser un entero, no decimal.')
            })

        if self.laboratorio and (len(self.laboratorio) < 2 or len(self.laboratorio) > 350):
            raise ValidationError({
                'laboratorio': _('Mínimo 2, máximo 350 caracteres.')
            })
        
        if self.fecha_caducidad is None or self.fecha_caducidad == "":
            raise ValidationError({
                'fecha_caducidad': _('Fecha de caducidad es obligatoria.')
            })

        if self.fecha_caducidad and self.fecha_caducidad < self.fecha_registro:
            raise ValidationError({
                'fecha_caducidad': _('No puede ser anterior al registro.')
            })

    def delete(self, using=None, keep_parents=False):
        if self.imagen_medicina:
            ruta_imagen = os.path.join(settings.MEDIA_ROOT, self.imagen_medicina.name)
            if os.path.isfile(ruta_imagen):
                os.remove(ruta_imagen)
        super().delete(using=using, keep_parents=keep_parents)


    def save(self, *args, **kwargs):
        es_nuevo = self.pk is None

        imagen_anterior = None
        if not es_nuevo:
            try:
                instancia_anterior = Medicina.objects.get(pk=self.pk)
                imagen_anterior = instancia_anterior.imagen_medicina
            except Medicina.DoesNotExist:
                pass
    
        carpeta_media = os.path.join(settings.MEDIA_ROOT, 'fotos_medicinas')
        os.makedirs(carpeta_media, exist_ok=True)
        super().save(*args, **kwargs)

        if self.imagen_medicina:
            nombre_viejo = self.imagen_medicina.name
            nombre_nuevo = fotos_medicinas_upload_path(self, os.path.basename(nombre_viejo))
        

            if nombre_viejo != nombre_nuevo:
                ruta_vieja = os.path.join(settings.MEDIA_ROOT, nombre_viejo)
                ruta_nueva = os.path.join(settings.MEDIA_ROOT, nombre_nuevo)

                if os.path.exists(ruta_nueva):
                    os.remove(ruta_nueva)
            
                if os.path.exists(ruta_vieja):
                    os.rename(ruta_vieja, ruta_nueva)
                    self.imagen_medicina.name = nombre_nuevo
                    super().save(update_fields=['imagen_medicina'])
        

            if (imagen_anterior and 
                imagen_anterior != self.imagen_medicina and 
                imagen_anterior.name != nombre_nuevo and
                os.path.isfile(os.path.join(settings.MEDIA_ROOT, imagen_anterior.name))):
                os.remove(os.path.join(settings.MEDIA_ROOT, imagen_anterior.name))


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
