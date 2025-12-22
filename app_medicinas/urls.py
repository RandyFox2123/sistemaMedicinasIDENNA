
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    #Autenticacion(Login)
    path('login/', views.login_ingreso, name="login"),
    path("cerrar_seccion/", views.cerrar_seccion, name="cerrar_seccion"),

    #General
    path('', views.index, name="index"),
    path('panel_principal/', views.panel_principal, name='panel_principal'),

    #Medicina
    path('registrar_medicina/', views.registrar_medicina, name='registrar_medicina'),
    path('edicion_medicina/<int:id_medicina>', views.editar_medicina, name='edicion_medicina'),
    path('ver_medicina/<int:id_medicina>', views.ver_medicina, name='ver_medicina'),
    path('borrar_medicina/<int:id_medicina>', views.borrar_medicina, name='borrar_medicina'),
    path('sumar_medicina/<int:id_medicina>', views.sumar_cantidad_medicina, name='sumar_medicina'),
    path('restar_medicina/<int:id_medicina>', views.restar_cantidad_medicina, name='restar_medicina'),
    path('caducidades/', views.caducidades, name='caducidades'),

    #Otros
    path('generar_excel/', views.generar_excel, name='generar_excel')
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
