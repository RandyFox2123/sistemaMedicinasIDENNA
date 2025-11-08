
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.urls import reverse
from django.core.paginator import Paginator
from django.views.decorators.http import require_safe, require_http_methods, require_POST
from openpyxl import Workbook
from  . models import Almacen, Medicina, Medida
import os
import logging
from django.conf import settings
from decimal import Decimal


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
def index(request):
    return render(request, 'index.html')


@manejo_errores
@require_safe
def panel_principal(request):
    almacenes_activos = Almacen.objects.filter(estado=True)
    filtro_desc_medicina = request.GET.get('filtro_desc_medicina', '').strip()
    filtro_almacen_id = request.GET.get('filtro_almacen', '').strip()
    page_num = request.GET.get('page', '')
    medicinas_qs = Medicina.objects.filter(almacen_perteneciente__estado=True)

    if filtro_desc_medicina:
        medicinas_qs = medicinas_qs.filter(desc_medicina__icontains=filtro_desc_medicina).order_by('-id_medicina')

    if filtro_almacen_id.isdigit():
        medicinas_qs = medicinas_qs.filter(almacen_perteneciente_id=int(filtro_almacen_id)).order_by('-id_medicina')

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
    if filtro_almacen_id:
        query_params.append(f"filtro_almacen={filtro_almacen_id}")
    if page_num:
        query_params.append(f"page={page_num}")

    url_con_filtros = reverse('panel_principal')
    if query_params:
        url_con_filtros += '?' + '&'.join(query_params)

    request.session['url_panel_principal'] = url_con_filtros

    contexto = {
        'page_obj': page_obj,
        'almacenes_activos': almacenes_activos,
        'filtro_desc_medicina': filtro_desc_medicina,
        'filtro_almacen_id': filtro_almacen_id,
    }
    return render(request, 'panel_principal.html', contexto)


@manejo_errores
@require_http_methods(["GET", "POST"])
def registrar_medicina(request):
    almacenes_activos = Almacen.objects.filter(estado=True)
    todas_medidas = Medida.objects.all()

    if request.method == 'POST':
        desc_medicina = request.POST.get('desc_medicina', '').strip()
        almacen_id = request.POST.get('almacen_perteneciente')
        imagen = request.FILES.get('imagen_medicina')
        cantidad_str = request.POST.get('cantidad', '0').strip()

        medida_recibida = request.POST.get('medida', None)
        if medida_recibida and medida_recibida.isdigit():
            medida_recibida = int(medida_recibida)
            if medida_recibida < 0:
                raise error_contexto("Se ha recibido un tipo de cantidad inválido")
            else:
                medida_obj = Medida.objects.filter(pk=medida_recibida).first()
        else:
            raise error_contexto("Se ha recibido un tipo de cantidad inválido")

        if Medicina.objects.filter(desc_medicina__iexact=desc_medicina).exists():
            raise error_contexto("Ya existe una medicina con esta descripción.")

        if not desc_medicina:
            raise error_contexto("La descripción es obligatoria.")

        try:
            cantidad = float(cantidad_str.replace(',', '.'))
            if cantidad < 0 or cantidad > 50000:
                raise error_contexto("La cantidad debe ser un número mayor o igual a 0 o máximo 50000")
        except ValueError:
            raise error_contexto("La cantidad debe ser un número válido.")

        almacen_obj = None
        if almacen_id and almacen_id.isdigit():
            almacen_obj = Almacen.objects.filter(pk=int(almacen_id), estado=True).first()

        nueva_medicina = Medicina(
            desc_medicina=desc_medicina,
            almacen_perteneciente=almacen_obj,
            cantidad=cantidad,
            medida_medicina=medida_obj,
        )
        if imagen:
            nueva_medicina.imagen_medicina = imagen
        nueva_medicina.save()

        url_redireccion = request.session.get('url_panel_principal', reverse('panel_principal'))
        return HttpResponseRedirect(url_redireccion)

    return render(request, 'registrar_medicina.html', {'almacenes_activos': almacenes_activos, "medidas": todas_medidas})


@manejo_errores
@require_http_methods(["GET", "POST"])
def editar_medicina(request, id_medicina):
    medicina_obj = get_object_or_404(Medicina, pk=id_medicina)
    almacenes_activos = Almacen.objects.filter(estado=True)
    cantidad_formateada_medicina_editada = str(medicina_obj.cantidad).replace(',', '.')
    medidas = Medida.objects.all()

    if request.method == 'POST':
        desc_medicina = request.POST.get('desc_medicina', '').strip()
        almacen_id = request.POST.get('almacen_perteneciente')
        nueva_imagen = request.FILES.get('imagen_medicina')
        cantidad_str = request.POST.get('cantidad', '').strip()
        desc_medicina_vieja = request.POST.get('desc_medicina_vieja', '').strip()

        if desc_medicina_vieja != desc_medicina:
            if Medicina.objects.filter(desc_medicina__iexact=desc_medicina).exists():
                raise error_contexto("Ya existe una medicina con esta descripción.")
        else:
            desc_medicina = desc_medicina_vieja

        if not desc_medicina:
            raise error_contexto("La descripción es obligatoria.")

        if cantidad_str == '':
            raise error_contexto("La cantidad es obligatoria.")

        try:
            cantidad = float(cantidad_str.replace(',', '.'))
            if cantidad < 0 or cantidad > 50000:
                raise error_contexto("La cantidad debe ser un número mayor o igual a 0 o máximo 50000")
            
        except ValueError:
            raise error_contexto("La cantidad debe ser un número válido.")

        almacen_obj = None
        if almacen_id and almacen_id.isdigit():
            almacen_obj = Almacen.objects.filter(pk=int(almacen_id), estado=True).first()

        if nueva_imagen:
            if medicina_obj.imagen_medicina and os.path.isfile(medicina_obj.imagen_medicina.path):
                os.remove(medicina_obj.imagen_medicina.path)
            medicina_obj.imagen_medicina = nueva_imagen

        medicina_obj.desc_medicina = desc_medicina
        medicina_obj.almacen_perteneciente = almacen_obj
        medicina_obj.cantidad = cantidad
        medicina_obj.save()

        url_redireccion = request.session.get('url_panel_principal', reverse('panel_principal'))
        return HttpResponseRedirect(url_redireccion)

    contexto = {
        'medicina_obj': medicina_obj,
        'almacenes_activos': almacenes_activos,
        'medidas': medidas,
        'medida_formateada' : cantidad_formateada_medicina_editada,
    }
    return render(request, 'editar_medicina.html', contexto)


@manejo_errores
@require_POST
def borrar_medicina(request, id_medicina):
    medicina_obj = get_object_or_404(Medicina, pk=id_medicina)

    if medicina_obj.imagen_medicina and os.path.isfile(medicina_obj.imagen_medicina.path):
        os.remove(medicina_obj.imagen_medicina.path)

    medicina_obj.delete()

    url_redireccion = request.session.get('url_panel_principal', reverse('panel_principal'))
    return HttpResponseRedirect(url_redireccion)


@manejo_errores
@require_POST
def sumar_cantidad_medicina(request, id_medicina):
    medicina = get_object_or_404(Medicina, pk=id_medicina)

    try:
        cantidad_sumar = request.POST.get('suma', '0').replace(',', '.')
        cantidad_sumar = Decimal(cantidad_sumar)

        if cantidad_sumar < 0:
            raise error_contexto("La cantidad a sumar no puede ser negativa.")
    except (ValueError, TypeError):
        raise error_contexto("Cantidad inválida.")

    medicina.cantidad += cantidad_sumar
    medicina.save()

    url_redireccion = request.session.get('url_panel_principal', reverse('panel_principal'))
    return HttpResponseRedirect(url_redireccion)


@manejo_errores
@require_POST
def restar_cantidad_medicina(request, id_medicina):
    medicina = get_object_or_404(Medicina, pk=id_medicina)

    try:
        cantidad_restar = request.POST.get('resta', '0').replace(',', '.')
        cantidad_restar = Decimal(cantidad_restar)

        if cantidad_restar < 0:
            raise error_contexto("La cantidad a restar no puede ser negativa.")

    except (ValueError, TypeError):
        raise error_contexto("Cantidad inválida.")

    nueva_cantidad = max(medicina.cantidad - cantidad_restar, Decimal('0'))
    medicina.cantidad = nueva_cantidad
    medicina.save()

    url_redireccion = request.session.get('url_panel_principal', reverse('panel_principal'))
    return HttpResponseRedirect(url_redireccion)


@manejo_errores
@require_safe
def generar_excel(request):
    filtro_desc_medicina = request.GET.get('filtro_desc_medicina', '').strip()
    filtro_almacen_id = request.GET.get('filtro_almacen', '').strip()

    medicinas_qs = Medicina.objects.filter(almacen_perteneciente__estado=True)

    if filtro_desc_medicina:
        medicinas_qs = medicinas_qs.filter(desc_medicina__icontains=filtro_desc_medicina)

    if filtro_almacen_id.isdigit():
        medicinas_qs = medicinas_qs.filter(almacen_perteneciente_id=int(filtro_almacen_id))

    medicinas_qs = medicinas_qs.order_by('id_medicina')

    wb = Workbook()
    ws = wb.active

    ws['A1'] = 'Descripción Medicina'
    ws['B1'] = 'Almacén'
    ws['C1'] = 'Cantidad'

    row = 2
    for medicina in medicinas_qs:
        ws[f'A{row}'] = medicina.desc_medicina
        ws[f'B{row}'] = medicina.almacen_perteneciente.desc_almacen if medicina.almacen_perteneciente else "Sin almacén"
        ws[f'C{row}'] = float(medicina.cantidad)
        row += 1

    nombre_archivo = "Reporte_Medicinas.xlsx"

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'

    wb.save(response)
    return response
