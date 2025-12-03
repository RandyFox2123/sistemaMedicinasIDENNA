

from django.contrib import admin
from . models import Medicina, Ubicacion, Presentacion_Medicamento

# Register your models here.
admin.site.register(Medicina)
admin.site.register(Ubicacion)
admin.site.register(Presentacion_Medicamento)
