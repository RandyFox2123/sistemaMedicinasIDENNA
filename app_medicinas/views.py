
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.urls import reverse
from django.core.paginator import Paginator
from django.views.decorators.http import require_safe, require_http_methods, require_POST
from openpyxl import Workbook
from  . models import Medicina, Ubicacion, Presentacion_Medicamento
import os
import logging
from django.conf import settings
from decimal import Decimal
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required



logger = logging.getLogger(__name__)

error_no_encontrado = 'Lo sentimos, el recurso que solicitas no fue encontrado'
error_inesperado = 'Lo sentimos, pero ha ocurrido un error inesperado en el proceso'
metodo_no_permitido = 'Lo sentimos, hubo un error, el método no está permitido, no se puede proceder por seguridad'

class error_contexto(Exception):
    pass

def manejo_errores(vista_recibida):
    def wrapper(request, *args, **kwargs):
        mensaje_error = None
        try:
            return vista_recibida(request, *args, **kwargs)

        except TypeError as e:
            mensaje_error = 'Lo sentimos, hubo un error interno en el proceso'
            logger.error(f'!!! ERROR OBTENIDO !!!:\n\n{e}')
            return render(request, 'error.html', {'error_obtenido': mensaje_error})

        except Http404 as e:
            mensaje_error = error_no_encontrado
            logger.error(f'!!! ERROR OBTENIDO !!!:\n\n{e}')
            return render(request, 'error.html', {'error_obtenido': mensaje_error})

        except Exception as error_obtenido:
            if isinstance(error_obtenido, error_contexto):
                mensaje_error = str(error_obtenido)
                logger.error(mensaje_error)
            else:
                mensaje_error = error_inesperado
                logger.error(f'{error_obtenido}')
            return render(request, 'error.html', {'error_obtenido': mensaje_error})

    return wrapper



@manejo_errores
@require_http_methods(["GET", "POST"])
def login_ingreso(request):
    contexto = {"mensaje" : None, "perfil" : None}
    
    if request.method == "GET":
        return render(request, 'registration/login.html')
    
    else:
        perfil_ingresado = request.POST.get("username", None)
        contrasena_ingresada = request.POST.get("password", None)
        
        if not perfil_ingresado or not contrasena_ingresada:
            contexto["mensaje"] = "Debes ingresar usuario y contraseña"
            contexto["perfil"] = perfil_ingresado
            return render(request, 'registration/login.html', contexto)
        
        
        #Buscamos el perfil, y si existe ingresamos
        try:
            perfil = User.objects.get(username=perfil_ingresado)
            if perfil:
                if perfil.is_active == False:
                    contexto["mensaje"] = "El perfil existe, pero está desactivado pongase en contacto con un usuario superior para que active este perfil."
                    contexto["perfil"] = perfil_ingresado
                    return render(request, 'registration/login.html', contexto)
            
                else:
                    autenticacion = authenticate(username=perfil_ingresado, password=contrasena_ingresada)
                    if autenticacion:
                        print("Ingreso exitoso")
                        login(request, perfil)
                        return redirect("panel_principal")
                    
                    else:
                        contexto["mensaje"] = "El perfil existe pero la contraseña introducida es invalida." 
                        contexto["perfil"] = perfil_ingresado
                        return render(request, 'registration/login.html', contexto)
        
        #El perfil no existe
        except  User.DoesNotExist:
            contexto["mensaje"] = "Lo sentimos, este perfil no existe."
            contexto["perfil"] = perfil_ingresado
            return render(request, 'registration/login.html', contexto)
            
             
@manejo_errores
@require_safe
def cerrar_seccion(request):
    logout(request)
    return redirect("/")




@manejo_errores
def index(request):
    return render(request, 'index.html')


@manejo_errores
@login_required
@require_safe
def panel_principal(request):
    ubicaciones_activas = Ubicacion.objects.filter(estado=True)
    filtro_desc_medicina = request.GET.get('filtro_desc_medicina', '').strip()
    filtro_ubicacion_id = request.GET.get('filtro_ubicacion', '').strip()
    page_num = request.GET.get('page', '')
    medicinas_qs = Medicina.objects.filter(ubicacion__estado=True)

    if filtro_desc_medicina:
        medicinas_qs = medicinas_qs.filter(desc_medicina__icontains=filtro_desc_medicina).order_by('-id_medicina')

    if filtro_ubicacion_id.isdigit():
        medicinas_qs = medicinas_qs.filter(ubicacion_id=int(filtro_ubicacion_id)).order_by('-id_medicina')

    paginator = Paginator(medicinas_qs.order_by('-id_medicina'), 3)
    page_obj = paginator.get_page(page_num)

    for medicina in page_obj:
        if medicina.imagen_medicina and medicina.imagen_medicina.name:
            ruta_imagen = os.path.join(settings.MEDIA_ROOT, medicina.imagen_medicina.name)
            medicina.imagen_existe = os.path.isfile(ruta_imagen)
        else:
            medicina.imagen_existe = False

    query_params = []
    if filtro_desc_medicina:
        query_params.append(f"filtro_desc_medicina={filtro_desc_medicina}")
    if filtro_ubicacion_id:
        query_params.append(f"filtro_ubicacion={filtro_ubicacion_id}")
    if page_num:
        query_params.append(f"page={page_num}")

    url_con_filtros = reverse('panel_principal')
    if query_params:
        url_con_filtros += '?' + '&'.join(query_params)

    request.session['url_panel_principal'] = url_con_filtros

    contexto = {
        'page_obj': page_obj,
        'ubicaciones_activas': ubicaciones_activas,
        'filtro_desc_medicina': filtro_desc_medicina,
        'filtro_ubicacion_id': filtro_ubicacion_id,
    }
    return render(request, 'panel_principal.html', contexto)

@manejo_errores
@login_required
@require_http_methods(["GET", "POST"])
def registrar_medicina(request):
    ubicaciones_activas = Ubicacion.objects.filter(estado=True)
    presentaciones = Presentacion_Medicamento.objects.all()

    if request.method == 'POST':
        desc_medicina = request.POST.get('desc_medicina', '').strip()
        ubicacion_id = request.POST.get('ubicacion_perteneciente')
        imagen = request.FILES.get('imagen_medicina')
        cantidad_str = request.POST.get('cantidad', '0').strip()

        if Medicina.objects.filter(desc_medicina__iexact=desc_medicina).exists():
            raise error_contexto("Ya existe una medicina con esta descripcion.")

        if not desc_medicina:
            raise error_contexto("La descripcion es obligatoria.")

        try:
            cantidad = float(cantidad_str.replace(',', '.'))
            if cantidad < 0 or cantidad > 50000:
                raise error_contexto("La cantidad debe ser un numero mayor o igual a 0 o maximo 50000")
        except ValueError:
            raise error_contexto("La cantidad debe ser un numero valido.")

        ubicacion_obj = None
        if ubicacion_id and ubicacion_id.isdigit():
            ubicacion_obj = Ubicacion.objects.filter(pk=int(ubicacion_id), estado=True).first()

        nueva_medicina = Medicina(
            desc_medicina=desc_medicina,
            ubicacion_perteneciente=ubicacion_obj,
            cantidad=cantidad,
        )
        if imagen:
            nueva_medicina.imagen_medicina = imagen
        nueva_medicina.save()

        url_redireccion = request.session.get('url_panel_principal', reverse('panel_principal'))
        return HttpResponseRedirect(url_redireccion)

    return render(request, 'registrar_medicina.html', {'ubicaciones_activas': ubicaciones_activas, 'presentaciones': presentaciones})

@manejo_errores
@login_required
@require_http_methods(["GET", "POST"])
def editar_medicina(request, id_medicina):
    medicina_obj = get_object_or_404(Medicina, pk=id_medicina)
    ubicaciones_activas = Ubicacion.objects.filter(estado=True)
    cantidad_formateada_medicina_editada = str(medicina_obj.cantidad).replace(',', '.')

    if request.method == 'POST':
        desc_medicina = request.POST.get('desc_medicina', '').strip()
        ubicacion_id = request.POST.get('ubicacion_perteneciente')
        nueva_imagen = request.FILES.get('imagen_medicina')
        cantidad_str = request.POST.get('cantidad', '').strip()
        desc_medicina_vieja = request.POST.get('desc_medicina_vieja', '').strip()

        if desc_medicina_vieja != desc_medicina:
            if Medicina.objects.filter(desc_medicina__iexact=desc_medicina).exists():
                raise error_contexto("Ya existe una medicina con esta descripcion.")
        else:
            desc_medicina = desc_medicina_vieja

        if not desc_medicina:
            raise error_contexto("La descripcion es obligatoria.")

        if cantidad_str == '':
            raise error_contexto("La cantidad es obligatoria.")

        try:
            cantidad = float(cantidad_str.replace(',', '.'))
            if cantidad < 0 or cantidad > 50000:
                raise error_contexto("La cantidad debe ser un numero mayor o igual a 0 o maximo 50000")
        except ValueError:
            raise error_contexto("La cantidad debe ser un numero valido.")

        ubicacion_obj = None
        if ubicacion_id and ubicacion_id.isdigit():
            ubicacion_obj = Ubicacion.objects.filter(pk=int(ubicacion_id), estado=True).first()

        if nueva_imagen:
            if medicina_obj.imagen_medicina and os.path.isfile(medicina_obj.imagen_medicina.path):
                os.remove(medicina_obj.imagen_medicina.path)
            medicina_obj.imagen_medicina = nueva_imagen

        medicina_obj.desc_medicina = desc_medicina
        medicina_obj.ubicacion_perteneciente = ubicacion_obj
        medicina_obj.cantidad = cantidad
        medicina_obj.save()

        url_redireccion = request.session.get('url_panel_principal', reverse('panel_principal'))
        return HttpResponseRedirect(url_redireccion)

    contexto = {
        'medicina_obj': medicina_obj,
        'ubicaciones_activas': ubicaciones_activas,
        'medida_formateada': cantidad_formateada_medicina_editada,
    }
    return render(request, 'editar_medicina.html', contexto)

@manejo_errores
@login_required
@require_POST
def borrar_medicina(request, id_medicina):
    medicina_obj = get_object_or_404(Medicina, pk=id_medicina)

    if medicina_obj.imagen_medicina and os.path.isfile(medicina_obj.imagen_medicina.path):
        os.remove(medicina_obj.imagen_medicina.path)

    medicina_obj.delete()

    url_redireccion = request.session.get('url_panel_principal', reverse('panel_principal'))
    return HttpResponseRedirect(url_redireccion)

@manejo_errores
@login_required
@require_POST
def sumar_cantidad_medicina(request, id_medicina):
    medicina = get_object_or_404(Medicina, pk=id_medicina)

    try:
        cantidad_sumar = request.POST.get('suma', '0').replace(',', '.')
        cantidad_sumar = Decimal(cantidad_sumar)

        if cantidad_sumar < 0:
            raise error_contexto("La cantidad a sumar no puede ser negativa.")
    except (ValueError, TypeError):
        raise error_contexto("Cantidad invalida.")

    medicina.cantidad += cantidad_sumar
    medicina.save()

    url_redireccion = request.session.get('url_panel_principal', reverse('panel_principal'))
    return HttpResponseRedirect(url_redireccion)

@manejo_errores
@login_required
@require_POST
def restar_cantidad_medicina(request, id_medicina):
    medicina = get_object_or_404(Medicina, pk=id_medicina)

    try:
        cantidad_restar = request.POST.get('resta', '0').replace(',', '.')
        cantidad_restar = Decimal(cantidad_restar)

        if cantidad_restar < 0:
            raise error_contexto("La cantidad a restar no puede ser negativa.")

    except (ValueError, TypeError):
        raise error_contexto("Cantidad invalida.")

    nueva_cantidad = max(medicina.cantidad - cantidad_restar, Decimal('0'))
    medicina.cantidad = nueva_cantidad
    medicina.save()

    url_redireccion = request.session.get('url_panel_principal', reverse('panel_principal'))
    return HttpResponseRedirect(url_redireccion)

@manejo_errores
@login_required
@require_safe
def generar_excel(request):
    filtro_desc_medicina = request.GET.get('filtro_desc_medicina', '').strip()
    filtro_ubicacion_id = request.GET.get('filtro_ubicacion', '').strip()

    medicinas_qs = Medicina.objects.filter(ubicacion_perteneciente__estado=True)

    if filtro_desc_medicina:
        medicinas_qs = medicinas_qs.filter(desc_medicina__icontains=filtro_desc_medicina)

    if filtro_ubicacion_id.isdigit():
        medicinas_qs = medicinas_qs.filter(ubicacion_perteneciente_id=int(filtro_ubicacion_id))

    medicinas_qs = medicinas_qs.order_by('id_medicina')

    wb = Workbook()
    ws = wb.active

    ws['A1'] = 'Descripcion Medicina'
    ws['B1'] = 'Ubicacion'
    ws['C1'] = 'Cantidad'

    row = 2
    for medicina in medicinas_qs:
        ws[f'A{row}'] = medicina.desc_medicina
        ws[f'B{row}'] = medicina.ubicacion_perteneciente.desc_ubicacion if medicina.ubicacion_perteneciente else "Sin ubicacion"
        ws[f'C{row}'] = float(medicina.cantidad)
        row += 1

    nombre_archivo = "Reporte_Medicinas.xlsx"

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'

    wb.save(response)
    return response
