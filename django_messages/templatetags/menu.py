# -*- coding: utf8 -*-
from django import template
from django.utils.html import escape
from django.utils.html import format_html

register = template.Library()
def menu(seccion):
    renderizar = ''

    titulos = []
    enlace = []
    clase = []
    vmenu=[]

    # Inicio
    titulos.append("Inicio")
    enlace.append("/")
    clase.append("nav1")

    # Memos
    titulos.append("Memos")
    enlace.append("/entrada/#Menu")
    clase.append("nav2")

    # Reportes
    titulos.append("Reportes")
    enlace.append("/reportes/#Menu")
    clase.append("nav4")

    # Perfil
    titulos.append("Perfil")
    enlace.append("/perfil/#Menu")
    clase.append("nav3")

    # Contactos
    titulos.append("Contactos")
    enlace.append("/contactos/#Menu")
    clase.append("nav5")

    vmenu.append(titulos)
    vmenu.append(enlace)

    activo = ''
    for posicion in range(titulos.__len__()):
        if titulos[posicion] == seccion:
            activo = 'id="active"'
        else:
            activo = ''
        url = '<li class='+ clase[posicion] +' '+ activo +'><a href='+ enlace[posicion] +'>'+ '<cufon class="cufon cufon-canvas" alt="' + titulos[posicion] + '" style="width: 80px; height: 24px;"><canvas width="88" height="29" style="width: 88px; height: 29px; top: -4px; left: -1px;"/><cufontext>' + titulos[posicion] + '</cufontext></cufon>' +'</a></li>'
        renderizar = renderizar + url


    return format_html(renderizar)
menu.is_safe = True 
register.filter(menu)

def num_entrada(request):
    from django_messages.models import Message, Destinatarios
    destinatario = Destinatarios.objects.get(usuarios__user=request.user)
    message_list = Message.objects.filter(recipient=destinatario, read_at__isnull=True, deleted_at__isnull=True).distinct()
    if not request.user.profile.persona.cargo_principal.cargo == request.user.profile.persona.cargo_principal.dependencia.cargo_max:
        message_list = message_list.filter(status__nombre__iexact='Aprobado')
    return message_list.count()
num_entrada.is_safe = True 
register.filter(num_entrada)

def jefe_departamento(request):
    if request.user.profile.persona.cargo_principal.cargo == request.user.profile.persona.cargo_principal.dependencia.cargo_max:
        return True
    else:
        return False
jefe_departamento.is_safe = True 
register.filter(jefe_departamento)

def por_aprobar(request):
    from django.db import models
    from django_messages.models import Message
    dependencia = request.user.profile.persona.cargo_principal.dependencia
    message_list = Message.objects.filter(models.Q( status__nombre__iexact='En espera', 
                                                    sender__usuarios__persona__cargo_principal__dependencia=dependencia)| 
                                          models.Q(sender__usuarios__persona__cargos_autorizados__dependencia=dependencia)).order_by('codigo').distinct('codigo')
    return message_list 
por_aprobar.is_safe = True 
register.filter(por_aprobar)

def num_por_aprobar(request):
    return por_aprobar(request).count() 
num_por_aprobar.is_safe = True 
register.filter(num_por_aprobar)

def estado(mensaje):
    from django_messages.models import Message
    from noticias.templatetags.disminuir import disminuir_t 
    mensaje = Message.objects.get(id=mensaje.id)
    # Color del fondo:
    color = ''
    if mensaje.status.nombre == 'En espera':
        color = "#69BAF4" # Azul
    elif mensaje.status.nombre == 'Aprobado':
        color = "#81F26A" # Verde
    elif mensaje.status.nombre == 'Anulado':
        color = "#EA4444" # Rojo

    estado_memo = '<div class="col_5" style="background-color:%s" align="center">%s</div> <div>%s...</div>' %(color, mensaje.status.nombre, disminuir_t(mensaje.subject, 40))
    return format_html(estado_memo)
estado.is_safe = True 
register.filter(estado)

def active(request, tipo_bandeja):
    if request.get_full_path().replace('/','').replace('bandeja','') == tipo_bandeja:
        return format_html('class="active"')
active.is_safe = True 
register.filter(active)

def respuesta_comentario(comentario):
    from reportes.models import Respuestas
    return Respuestas.objects.get(pregunta=comentario).id
respuesta_comentario.is_safe = True 
register.filter(respuesta_comentario)

def nombre_iniciales(dest):
    import re
    m = re.findall('([A-Z])[A-Za-z]* *', "%s %s %s %s"%(dest.usuarios.persona.primer_nombre, dest.usuarios.persona.segundo_nombre, dest.usuarios.persona.primer_apellido, dest.usuarios.persona.segundo_apellido ))
    iniciales = "".join(m)
    return iniciales
nombre_iniciales.is_safe = True 
register.filter(nombre_iniciales)

def primero(paginador):
    return '?page=1'
primero.is_safe = True 
register.filter(primero)

def ultimo(paginador):
    return '?page=%s' %(paginador.paginator.num_pages)
ultimo.is_safe = True 
register.filter(ultimo)

def anterior(paginador):
    if paginador.has_previous():
        return '?page=%s' %(paginador.previous_page_number())
    else:
        return '#'
anterior.is_safe = True 
register.filter(anterior)

def siguiente(paginador):
    if paginador.has_next():
        return '?page=%s' %(paginador.next_page_number())
    else:
        return '#'
siguiente.is_safe = True 
register.filter(siguiente)
