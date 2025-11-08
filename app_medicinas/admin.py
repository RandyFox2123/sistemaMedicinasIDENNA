from django.contrib import admin
from . models import Medicina, Medida, Almacen

# Register your models here.
admin.site.register(Medicina)
admin.site.register(Medida)
admin.site.register(Almacen)