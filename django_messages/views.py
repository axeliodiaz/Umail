# -*- coding: utf-8 -*-
import datetime
from django.views.generic.base import View
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.template import RequestContext
from django.template.context_processors import csrf
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from lib.umail import msj_expresion, renderizar_plantilla
from django.utils.translation import gettext as _
import json as simplejson
from django.http import HttpResponse
from django.utils.translation import gettext_noop
from django.db.models import Q
from django_messages.models import Destinatarios, EstadoMemo
from django.urls import reverse
from django.conf import settings
from django.db import models
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django_messages.models import Message
from django_messages.forms import ComposeForm, BandejaForm
from django_messages.utils import format_quote
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.models import LogEntry, ADDITION, DELETION, CHANGE
from django.forms.models import modelformset_factory
from umail import settings

if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification
else:
    notification = None

def anular(request, message_id):
    if request.user.profile.persona.cargo_principal.cargo == request.user.profile.persona.cargo_principal.dependencia.cargo_max:
        from django_messages.models import EstadoMemo
        mensaje = Message.objects.get(id=message_id)
        estado = EstadoMemo.objects.get(nombre='Anulado')
        mensaje.status = estado
        mensaje.save()
        return por_aprobar(request, mensaje='Memorándum anulado exitosamente')
    else:
        raise Http404
anular = login_required(anular, login_url='/auth')


def aprobar(request, message_id):
    if request.user.profile.persona.cargo_principal.cargo == request.user.profile.persona.cargo_principal.dependencia.cargo_max:
        from django_messages.models import EstadoMemo, Destinatarios
        mensaje = Message.objects.get(id=message_id)
        estado = EstadoMemo.objects.get(nombre='Aprobado')
        mensaje.status = estado
        mensaje.save()
        return por_aprobar(request, mensaje='Memorándum aprobado exitosamente')
    else:
        raise Http404
aprobar = login_required(aprobar, login_url='/auth')

def por_aprobar(request, mensaje=''):
    """
    Displays a list of received messages for the current user.
    Optional Arguments:
        ``template_name``: name of the template to use.
    """
    notify = False
    if not mensaje == '':
        notify = True
    if request.user.is_authenticated:
        dependencia = request.user.profile.persona.cargo_principal.dependencia
        # Lista de mensajes en espera escritos por la dependencia del jefe de dependencia
        message_list = Message.objects.filter(models.Q( status__nombre__iexact='En espera', 
                                                        sender__usuarios__persona__cargo_principal__dependencia=dependencia)| 
                                              models.Q(sender__usuarios__persona__cargos_autorizados__dependencia=dependencia))
        if not message_list.exists():
            mensaje = 'No tiene ningún mensaje por aprobar hasta ahora'
        return render(request, 'user/mensajes/bandeja.html', {
            'message_list': message_list,
            'loggeado': request.user.is_authenticated,
            'request':request,
            'mensaje':mensaje,
            'notify':notify,
        })
    else:
        return HttpResponseRedirect('/')

def ver_por_aprobar(request, message_id, template_name='user/mensajes/leer_aprobado.html'):
    """
    Shows a single message.``message_id`` argument is required.
    The user is only allowed to see the message, if he is either 
    the sender or the recipient. If the user is not allowed a 404
    is raised. 
    If the user is the recipient and the message is unread 
    ``read_at`` is set to the current datetime.
    """
    user = request.user
    if user.profile.persona.cargo_principal.cargo == user.profile.persona.cargo_principal.dependencia.cargo_max:
        now = datetime.datetime.now()
        message = get_object_or_404(Message, id=message_id)
        esta_destinatario = False
        
        message_list = Message.objects.filter(models.Q(status__nombre__iexact='En espera', sender__usuarios__persona__cargo_principal__dependencia=request.user.profile.persona.cargo_principal.dependencia)| models.Q(sender__usuarios__persona__cargos_autorizados__dependencia=request.user.profile.persona.cargo_principal.dependencia))

    else:
        raise Http404

    return render(request, template_name, {
        'loggeado': request.user.is_authenticated,
        'request':request,
        'message': message,
        'message_list': message_list,
    })
ver_por_aprobar = login_required(ver_por_aprobar, login_url='/auth')

def bandeja(request, tipo_bandeja='', expresion='', tipo_mensaje='', mensaje=''):
    """
    Displays a list of received messages for the current user.
    Optional Arguments:
        ``template_name``: name of the template to use.
    """
    notify = False
    diccionario = {}
    diccionario.update(csrf(request))
    if request.user.is_authenticated:
        if request.method == "POST":
            form = BandejaForm(request.POST)
            now = datetime.datetime.now()

            # Revisar si hay POST con archivar
            if 'archivar' in request.POST:
                lista = request.POST.getlist('seleccion')
                if lista.__len__() == 0:
                    form.errors.update({'mensajes':'No seleccionó ningún mensaje'})
                    tipo_mensaje = 'error'
                    mensaje = form.errors['mensajes']
                else:
                    lista_memos = []
                    for num in lista:
                        lista_memos.append(int(num))

                    # Buscar los memos según los ids que llegan
                    lista_memos = Message.objects.filter(id__in=lista_memos)

                    total_memos = lista_memos.count()
                    if lista_memos.exclude(status__nombre = 'En espera').count() == total_memos:
                        tipo_mensaje = 'success'
                        mensaje = 'Un total de %s mensajes fueron archivados' %(total_memos)
                    else:
                        tipo_mensaje = 'error'
                        mensaje = 'Los memorándum en espera que no pueden ser archivados. '
                        if lista_memos.exclude(status__nombre = 'En espera').count() > 1:
                            mensaje = mensaje + 'Sin embargo, %s memos fueron archivados' %(lista_memos.exclude(status__nombre = 'En espera').count())
                        elif lista_memos.exclude(status__nombre = 'En espera').count() == 1:
                            mensaje = mensaje + 'Sin embargo, %s memo fue archivado.' %(lista_memos.exclude(status__nombre = 'En espera').count())

                    for memo in lista_memos.exclude(status__nombre = 'En espera'):
                        # Se filtran los memos con el código del memo con el id filtrado anteriormente
                        memos = Message.objects.filter(codigo = memo.codigo).exclude(status__nombre = 'En espera')
                        for memorandum in memos:
                            memorandum.deleted_at = now
                            # Guardar log de memo archivado
                            LogEntry.objects.create(
                            user_id         = request.user.pk, 
                            content_type_id = ContentType.objects.get_for_model(Message).id,
                            object_id       = memorandum.id,
                            object_repr     = repr(memo), 
                            change_message  = mensaje,
                            action_flag     = DELETION
                            )
                            memorandum.save()


        form = BandejaForm()

        if tipo_bandeja == 'archivados': # ARCHIVADOS
            sender = Destinatarios.objects.get(usuarios__user=request.user)
            dependencia = request.user.profile.persona.cargo_principal.dependencia
            message_list = Message.objects.filter(models.Q(sender=sender) | models.Q(recipient=sender), deleted_at__isnull=False).order_by('codigo').distinct('codigo')

        if tipo_bandeja == 'por_aprobar': # POR APROBAR
            sender = Destinatarios.objects.get(usuarios__user=request.user)
            dependencia = request.user.profile.persona.cargo_principal.dependencia
            message_list = Message.objects.filter(models.Q(status__nombre__iexact='En espera', sender__usuarios__persona__cargo_principal__dependencia=dependencia)| models.Q(sender__usuarios__persona__cargos_autorizados__dependencia=dependencia)).order_by('codigo').distinct('codigo')

        if tipo_bandeja == 'borradores': # BORRADORES
            sender = Destinatarios.objects.get(usuarios__user=request.user)
            message_list = Message.objects.filter(sender=sender, borrador=True).order_by('codigo').distinct('codigo')

        if tipo_bandeja == 'enviados': # ENVIADOS
            destinatarios = Destinatarios.objects.filter(models.Q(usuarios__user=request.user)|models.Q(grupos__user=request.user))

            # Si es el jefe maximo, deben aparecer todos los memos de esa dependencia
            if request.user.profile.persona.cargo_principal.cargo == request.user.profile.persona.cargo_principal.dependencia.cargo_max:
                message_list = Message.objects.filter(sender__usuarios__persona__cargo_principal__dependencia=request.user.profile.persona.cargo_principal.dependencia, status__nombre__iexact='Aprobado')
            else:
                message_list = Message.objects.filter(sender__in=destinatarios)

        destinatario = Destinatarios.objects.get(usuarios__user=request.user)
        if tipo_bandeja == 'entrada': # ENTRADA
            message_list = Message.objects.filter(recipient=destinatario, deleted_at__isnull=True).distinct()
            if not request.user.profile.persona.cargo_principal.cargo == request.user.profile.persona.cargo_principal.dependencia.cargo_max:
                message_list = message_list.filter(status__nombre__iexact='Aprobado')

        if 'filtro' in request.POST:
            filtro = request.POST['filtro']
            if not filtro == '':
                message_list = Message.objects.filter(deleted_at__isnull=True).distinct()
                message_list = message_list.filter(Q(subject__icontains=filtro)| 
                                                   Q(body__icontains=filtro)| 
                                                   Q(sender__usuarios__persona__primer_nombre__icontains=filtro)| 
                                                   Q(sender__usuarios__persona__primer_apellido__icontains=filtro)|
                                                   Q(sender__usuarios__persona__segundo_nombre__icontains=filtro)|
                                                   Q(sender__usuarios__persona__segundo_apellido__icontains=filtro)| 
                                                   Q(recipient__usuarios__persona__cargo__dependencia__departamento__icontains=filtro)|
                                                   Q(sender__usuarios__persona__cargo__dependencia__departamento__icontains=filtro)|
                                                   Q(recipient__grupos__name__icontains=filtro)|
                                                   Q(recipient__usuarios__persona__primer_nombre__icontains=filtro)|
                                                   Q(recipient__usuarios__persona__primer_apellido__icontains=filtro)|
                                                   Q(recipient__usuarios__persona__segundo_nombre__icontains=filtro)| 
                                                   Q(recipient__usuarios__persona__segundo_apellido__icontains=filtro)| 
                                                   Q(status__nombre__iexact=filtro)| 
                                                   Q(codigo__iexact=filtro)|
                                                   Q(num_ident__iexact=filtro)
                                    )

        message_list = message_list.order_by('codigo','con_copia').distinct('codigo')
        if not message_list.exists() and mensaje == '':
            if 'filtro' in request.POST:
                mensaje = 'No se consiguió ningún mensaje'
            else:
                mensaje = 'No tiene ningún mensaje hasta ahora'
            (tipo_mensaje, expresion) = msj_expresion('info')
        
        # Revisar si hay algún orden
        if 'ver' in request.GET:
            opcion = request.GET['ver']
            if opcion == 'leido':
                # Excluir los que no están sin leer
                message_list = message_list.exclude(read_at=None)
            if opcion == 'no_leido':
                # Filtrar los que están sin leer
                message_list = message_list.filter(read_at=None)
            if opcion == 'apro':
                # Filtrar los que tengan estatus con nombre 'Aprobado'
                message_list = message_list.filter(status__nombre='Aprobado')
            if opcion == 'espera':
                # Filtrar los que tengan estatus con nombre 'Aprobado'
                message_list = message_list.filter(status__nombre='En espera')
            if opcion == 'anulado':
                # Filtrar los que tengan estatus con nombre 'Aprobado'
                message_list = message_list.filter(status__nombre='Anulado')


        paginador = Paginator(message_list, settings.SUIT_CONFIG['LIST_PER_PAGE'])
        page = request.GET.get('page')
        try:
            message_list = paginador.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            message_list = paginador.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            message_list = paginador.page(paginator.num_pages)

        diccionario.update({'request':request})
        diccionario.update({'message_list':message_list})
        diccionario.update({'tipo_mensaje':tipo_mensaje})
        diccionario.update({'expresion':expresion})
        diccionario.update({'mensaje':mensaje})
        diccionario.update({'tipo_bandeja':tipo_bandeja})
        diccionario.update({'nombre_action':'buscar_memos'})

        return render(request, 'usuario/mensajes/bandejas.html', diccionario)
    else:
        return HttpResponseRedirect('/')

def outbox(request, mensaje='', template_name='usuario/mensajes/bandejas.html'):
    """
    Displays a list of sent messages by the current user.
    Optional arguments:
        ``template_name``: name of the template to use.
    """
    message_list = Message.objects.outbox_for(request.user)
    mensajes = message_list
    paginador = Paginator(message_list, 20)
    page = request.GET.get('page')
    try:
        message_list = paginador.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        message_list = paginador.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        message_list = paginador.page(paginator.num_pages)
    if not mensajes.exists():
        mensaje = 'No tiene ningún mensaje hasta ahora'
    return render(request, template_name, {
        'request':request,
        'mensaje':mensaje,
        'message_list': message_list,
        'tipo_bandeja':'enviados',
    })
outbox = login_required(outbox, login_url='/auth')

def trash(request, template_name='user/mensajes/bandeja.html', mensaje=''):
    """
    Displays a list of deleted messages. 
    Optional arguments:
        ``template_name``: name of the template to use
    Hint: A Cron-Job could periodicly clean up old messages, which are deleted
    by sender and recipient.
    """
    message_list = Message.objects.trash_for(request.user)
    mensajes = message_list
    paginador = Paginator(message_list, 20)
    page = request.GET.get('page')
    try:
        message_list = paginador.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        message_list = paginador.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        message_list = paginador.page(paginator.num_pages)
    if not mensajes.exists():
        mensaje = 'No tiene ningún mensaje hasta ahora'
    return render(request, template_name, {
        'message_list': message_list,
        'mensaje':mensaje,
        'request':request,
    })
trash = login_required(trash, login_url='/auth')

def compose(request, message_id=None,
        template_name='usuario/mensajes/redactar.html', success_url=None, recipient_filter=None):
    """
    Displays and handles the ``form_class`` form to compose new messages.
    Required Arguments: None
    Optional Arguments:
        ``recipient``: username of a `django.contrib.auth` User, who should
                       receive the message, optionally multiple usernames
                       could be separated by a '+'
        ``form_class``: the form-class to use
        ``template_name``: the template to use
        ``success_url``: where to redirect after successfull submission
    """
    form_errors = ''

    (tipo_mensaje, expresion) = msj_expresion('alert')
    mensaje = 'El mensaje será guardado como borrador automáticamente cada 5 minutos'
    message = None
    if request.method == "POST":
        form = ComposeForm(request.POST)
        cuerpo = ''
        valido = form.is_valid()

        # Revisar si hay quien apruebe en el departamento del redactor
        jefe = Destinatarios.objects.filter(usuarios__user__userprofile__persona__cargo_principal__dependencia = request.user.profile.persona.cargo_principal.dependencia, usuarios__user__userprofile__persona__cargo_principal__cargo = request.user.profile.persona.cargo_principal.dependencia.cargo_max)
        if not jefe.exists():
            mensaje = 'Este memo no puede ser enviado ni aprobado porque no existe un jefe de departamento en %s' %(request.user.profile.persona.cargo_principal.dependencia)
            valido = False
        else:
            jefe = jefe[0]

        if valido:
            if 'recipient' in request.POST:
                destinatarios = form.cleaned_data['recipient']
                destinos = []
                for dest in destinatarios:
                    if dest.usuarios == None:
                        destinatarios2 = Destinatarios.objects.filter(usuarios__persona__cargo_principal__cargo=dest.grupos)
                        for dest2 in destinatarios2:
                            if not dest2 in form.cleaned_data['recipient']:
                                destinos.append(dest2)
                    else:
                        destinos.append(dest)
                destinatarios = destinos
            else:
                destinatarios = None

            if 'con_copia' in request.POST:
                con_copia = form.cleaned_data['con_copia']
            else:
                con_copia = None

            if 'archivo' in request.POST:
                archivo = request.POST['archivo']
            else:
                archivo = None

            sender = Destinatarios.objects.get(usuarios__user=request.user)

            # Revisar si se envió el formulario como borrador
            borrador = False
            enviar = False
            plantilla = False
            if 'borrador' in request.POST:
                borrador = True
            if 'enviar' in request.POST:
                enviar = True
            if 'plantilla' in request.POST:
                plantilla = True

            if enviar:
                mensaje = 'Mensaje enviado exitosamente'
            elif borrador:
                mensaje = 'Borrador guardado exitosamente'

            elif plantilla:
                print("Aún no programado")
                mensaje = 'Plantilla guardada exitosamente'

            # Por cada destinatario, enviar el memo, generar un log y enviar correo si está en la opción de envío
            if message_id:
                msjs_guardados = Message.objects.get(id=message_id)
                body = request.POST['body']
                subject = request.POST['subject']
                num_ident = msjs_guardados.num_ident
                codigo = msjs_guardados.codigo

                # Enlazar los destinatarios con los con_copia
                destinos = []

                if destinatarios:
                    for dest in destinatarios:
                        destinos.append(dest)
                if con_copia:
                    for dest_cc in con_copia:
                        destinos.append(dest_cc)
                '''
                if not destinatarios or not con_copia:
                    message = Message.objects.get(id=message_id)
                    message.body = body
                    message.subject = subject
                    message.archivo = archivo
                    message.borrador = borrador
                    message.save()
                '''


                msjs_guardados = Message.objects.filter(codigo=codigo)
                for dest in destinos:
                    # Si el destinatario no está en el campo 'recipient', entonces está en 'con_copia'
                    if not dest in destinatarios:
                        cc = True
                    else:
                        cc = False

                    # Si con ese codigo, están los mismos destinatarios, entonces se guarda la información
                    if msjs_guardados.filter(recipient=dest).exists():
                        message = Message.objects.get(recipient=dest, codigo=codigo)
                        message.recipient = dest
                        message.body = body
                        message.subject = subject
                        message.archivo = archivo
                        message.borrador = borrador
                        message.con_copia = cc

                        message.save()

                    # Si no existe, se crea
                    else:
                        message = crear_mensaje(
                                    destino=dest, 
                                    envio=sender, 
                                    asunto=subject, 
                                    cc=cc,
                                    cuerpo=body, 
                                    num_ident=msjs_guardados[0].num_ident,
                                    codigo=msjs_guardados[0].codigo,
                                    borrador=borrador,
                                    archivo = archivo,
                                    )
                # Eliminar memos cuyos destinatarios hayan sido excluidos
                if destinos:
                    msjs_guardados = msjs_guardados.exclude(recipient__in=destinos)
                    if msjs_guardados.exists():
                        msjs_guardados.delete()

            else:
                fecha_actual = datetime.datetime.today()
                mensajes = Message.objects.filter(sender__usuarios__user__userprofile__persona__cargo_principal__dependencia=sender.usuarios.user.profile.persona.cargo_principal.dependencia, sent_at__year=fecha_actual.year, sent_at__month=fecha_actual.month)
                num_ident = mensajes.count() + 1

                # El identificador se genera a partir del id del memo, del jefe de departamento y del minuto, segundo y microsegundo actual
                identificador = '%s%s' %(Message.objects.all().count(), jefe.id)

                codigo = ''
                for ident in identificador:
                    codigo = codigo + str(ord(ident))
                codigo = codigo + str(datetime.datetime.today().microsecond)

                if destinatarios:
                    for destino in destinatarios:
                        message = crear_mensaje(
                                    destino=destino, 
                                    envio=sender, 
                                    asunto=request.POST['subject'], 
                                    cuerpo=request.POST['body'], 
                                    cc=False,
                                    num_ident=num_ident,
                                    codigo=codigo,
                                    borrador=borrador,
                                    archivo=archivo,
                                    )
                elif con_copia:
                    for destino_cc in con_copia:
                        message = crear_mensaje(
                                    destino=destino_cc, 
                                    envio=sender, 
                                    asunto=request.POST['subject'], 
                                    cuerpo=request.POST['body'], 
                                    cc=True,
                                    num_ident=num_ident,
                                    codigo=codigo,
                                    borrador=borrador,
                                    archivo=archivo,
                                    )
                else:
                    message = crear_mensaje(
                                destino=None, 
                                envio=sender, 
                                asunto=request.POST['subject'], 
                                cuerpo=request.POST['body'], 
                                cc=False,
                                num_ident=num_ident,
                                codigo=codigo,
                                borrador=borrador,
                                archivo=archivo,
                                )
            # ¿Necesita el jefe recibir directamente el memorándum?
            '''
            if enviar and not destinatarios.__contains__(jefe):
                destino = jefe,
                message = crear_mensaje(
                            destino=destino, 
                            envio=sender, 
                            asunto=request.POST['subject'], 
                            cuerpo=request.POST['body'], 
                            cc=False,
                            num_ident=num_ident,
                            codigo=codigo,
                            borrador=borrador,
                            archivo=archivo,
                            )
            '''
        
            (tipo_mensaje, expresion) = msj_expresion('success')
            
            if success_url is None:
                success_url = reverse('messages_inbox')
            if 'next' in request.GET:
                success_url = request.GET['next']

        form.body = request.POST['body']
        if form.errors or not valido:
            (tipo_mensaje, expresion) = msj_expresion('error')
            label = ""
            if list(form.errors.keys())[0] == 'subject':
                label = "Asunto"
            elif list(form.errors.keys())[0] == 'recipient':
                label = "Destinatarios"
            elif list(form.errors.keys())[0] == 'body':
                label = "Texto"

            if not label == "":
                mensaje =  label + ': ' + list(form.errors.values())[0][0]

            if '__all__' in form.errors:
                mensaje = form.errors['__all__'].as_text().split('* ')[1]

        if form.errors or not valido:
            return render(request, template_name, {
                'tipo': 'Redactar',
                'tipo_mensaje':tipo_mensaje,
                'mensaje':mensaje,
                'message':message,
                'expresion':expresion,
                'request': request,
                'form': form,
            })

        elif 'borrador' in request.POST:
            return HttpResponseRedirect('/redactar/%s/' %(message.id))

        return bandeja(request, tipo_bandeja='enviados', expresion=expresion, tipo_mensaje=tipo_mensaje, mensaje=mensaje)
    else:
        form = ComposeForm()
        if message_id:
            message = Message.objects.get(id=message_id)
            if message.status.nombre == 'Aprobado':
                (tipo_mensaje, expresion) = msj_expresion('error')
                mensaje = 'Ese mensaje ya ha sido aprobado. No puede ser editado'
                return bandeja(request, tipo_bandeja='enviados', expresion=expresion, tipo_mensaje=tipo_mensaje, mensaje=mensaje)
            messages = Message.objects.filter(codigo=message.codigo)
            messages_cc = messages.filter(con_copia=True)
            messages = messages.filter(con_copia=False)
            dest_cc = []
            dest = []
            if messages_cc.exists():
                for msj in messages_cc:
                    dest_cc.append(msj.recipient)

            if messages.exists():
                for msj in messages:
                    dest.append(msj.recipient)

            form.fields['recipient'].initial = dest
            form.fields['body'].initial = message.body
            form.fields['con_copia'].initial = dest_cc
            form.fields['subject'].initial = message.subject
            form.fields['archivo'].initial = message.archivo
                
        else:
            persona = "%s.</br /> %s de %s" %(request.user.profile.persona, request.user.profile.persona.cargo_principal.cargo, request.user.profile.persona.cargo_principal.dependencia)
            form.fields['body'].initial = "<br /><br />Sin otro particular al cual hacer referencia, se despide. </br /></br /><b>Atentamente,</br /> %s</b>" %(persona.upper())
    return render(request, template_name, {
        'tipo': 'Redactar',
        'tipo_mensaje':tipo_mensaje,
        'mensaje':mensaje,
        'message':message,
        'expresion':expresion,
        'request': request,
        'form': form,
    })
compose = login_required(compose, login_url='/auth')

def crear_mensaje(destino='', 
                  envio='', 
                  archivo=None,
                  cc=False, 
                  asunto='', 
                  cuerpo='', 
                  num_ident='', 
                  codigo='', 
                  borrador=False,
                  log=True):
    '''
    Función para crear mensajes. Recibe parámetros:
    destino: usuario destinatario
    envio: usuario que lo envía
    cc: con copia. Por defecto Falso
    asunto: resumen del mensaje
    cuerpo: texto general del mensaje
    tipo: circular o personal
    log: Crea un log en LogEntry. Por defecto activo
    '''
    # Crear el mensaje a todas las personas en estado 'En espera'
    estado_memo = EstadoMemo.objects.get(nombre='En espera')

    mensaje = Message.objects.create(
                    recipient = destino,
                    sender = envio,
                    con_copia=cc,
                    subject = asunto,
                    body = cuerpo,
                    tipo = '',
                    status = estado_memo,
                    num_ident = num_ident,
                    codigo=codigo,
                    borrador=borrador,
                    archivo=archivo,
                )
    return mensaje

    mensaje_txt = 'Mensaje enviado exitosamente'
    # Guardar log de envío de memo
    LogEntry.objects.create(
        user_id         = envio.usuarios.user.pk, 
        content_type_id = ContentType.objects.get_for_model(Message).id,
        object_id       = mensaje.id,
        object_repr     = repr(mensaje), 
        change_message  = mensaje_txt,
        action_flag     = ADDITION
    )


def reply(request, message_id, form_class=ComposeForm,
    template_name='user/mensajes/redactar.html', success_url=None, 
        recipient_filter=None, quote_helper=format_quote):
    """
    Prepares the ``form_class`` form for writing a reply to a given message
    (specified via ``message_id``). Uses the ``format_quote`` helper from
    ``messages.utils`` to pre-format the quote. To change the quote format
    assign a different ``quote_helper`` kwarg in your url-conf.
    
    """
    parent = get_object_or_404(Message, id=message_id)
    
    user = request.user
    now = datetime.datetime.now()
    esta_destinatario = False

    for destinatario in parent.con_copia.all():
        if destinatario.grupos == None:
            if destinatario.usuarios.user == user:
                esta_destinatario = True
                continue
        elif destinatario.usuarios == None:
            if user in destinatario.grupos.user_set.all():
                esta_destinatario = True
                continue

    for destinatario in parent.recipient.all():
        if destinatario.grupos == None:
            if destinatario.usuarios.user == user:
                esta_destinatario = True
                continue
        elif destinatario.usuarios == None:
            if user in destinatario.grupos.user_set.all():
                esta_destinatario = True
                continue

    if (parent.sender != user) and (esta_destinatario == False):
        raise Http404
    
    if request.method == "POST":
        sender = request.user
        form = form_class(request.POST)
        if form.is_valid():
            estado_memo = EstadoMemo.objects.get(nombre='En espera')
            mensaje = Message(
                            sender = Destinatarios.objects.get(usuarios__user=request.user),
                            subject = request.POST['subject'],
                            body = request.POST['body'],
                            status = estado_memo,
                            parent_msg = parent,
                        )
            mensaje.save()
            dest = []
            for i in request.POST['recipient'].split('|'):
                if not i == '':
                    dest.append(int(i))
            for destin in dest:
                sender = Destinatarios.objects.filter(id=destin)
                if sender.exists():
                    mensaje.recipient.add(sender[0])
            mensaje.save()
            mensaje_txt = "Mensaje enviado exitosamente."

            # Guardar log de envío de memo
            LogEntry.objects.create(
            user_id         = request.user.pk, 
            content_type_id = ContentType.objects.get_for_model(Message).id,
            object_id       = mensaje.id,
            object_repr     = repr(mensaje), 
            change_message  = mensaje_txt,
            action_flag     = ADDITION
            )
            mensaje = mensaje_txt

                    
            return inbox(request, mensaje)
    else:
        cuerpo = "\n\n%s escribió:\n%s" %(parent.sender, parent.body)
        recipient = parent.recipient.add(parent.sender)
        destins = []
        for recip in parent.recipient.all():
            destins.append(recip.id)
        form = form_class(initial={
            'subject': _("Re: %(subject)s") % {'subject': parent.subject},
            'body': cuerpo,
            'recipient': destins
            })
    return render(request, template_name, {
        'tipo': 'Responder',
        'request': request,
        'form': form,
    })
reply = login_required(reply, login_url='/auth')

def delete(request, message_id, success_url=None):
    """
    Marks a message as deleted by sender or recipient. The message is not
    really removed from the database, because two users must delete a message
    before it's save to remove it completely. 
    A cron-job should prune the database and remove old messages which are 
    deleted by both users.
    As a side effect, this makes it easy to implement a trash with undelete.
    
    You can pass ?next=/foo/bar/ via the url to redirect the user to a different
    page (e.g. `/foo/bar/`) than ``success_url`` after deletion of the message.
    """
    user = request.user
    now = datetime.datetime.now()
    message = get_object_or_404(Message, id=message_id)
    deleted = False
    notify = False
    if success_url is None:
        success_url = reverse('messages_inbox')
    if 'next' in request.GET:
        success_url = request.GET['next']
    if message.sender.usuarios.user == user:
        message.sender_deleted_at = now
        deleted = True
    for destinatario in message.recipient.all():
        if destinatario.grupos == None:
            if destinatario.usuarios.user.username == user.username:
                message.recipient_deleted_at = now
                deleted = True
        elif destinatario.usuarios == None:
            if user in destinatario.grupos.user_set.all():
                message.recipient_deleted_at = now
                deleted = True
    if deleted:
        if message.status == 'En espera':
            message.save()
            mensaje_txt = "Mensaje archivado exitosamente."

            # Guardar log de memo archivado
            LogEntry.objects.create(
            user_id         = request.user.pk, 
            content_type_id = ContentType.objects.get_for_model(Message).id,
            object_id       = message.id,
            object_repr     = repr(message), 
            change_message  = mensaje_txt,
            action_flag     = DELETION
            )
            mensaje = mensaje_txt
        else:
            mensaje = 'Un mensaje que está en espera de ser aprobado no puede ser archivado aún.'
        notify = True
        if notification:
            notification.send([user], "messages_deleted", {'message': message,})
        return inbox(request, mensaje)
    raise Http404
delete = login_required(delete, login_url='/auth')

def undelete(request, success_url=None):
    """
    Recovers a message from trash. This is achieved by removing the
    ``(sender|recipient)_deleted_at`` from the model.
    """
    user = request.user
    message = get_object_or_404(Message, id=message_id)
    undeleted = False
    if success_url is None:
        success_url = reverse('messages_inbox')
    if 'next' in request.GET:
        success_url = request.GET['next']
    if message.sender == user:
        message.sender_deleted_at = None
        undeleted = True
    if message.recipient == user:
        message.recipient_deleted_at = None
        undeleted = True
    if undeleted:
        message.save()
        messages.info(request, _("Message successfully recovered."))
        if notification:
            notification.send([user], "messages_recovered", {'message': message,})
        return HttpResponseRedirect(success_url)
    raise Http404
undelete = login_required(undelete, login_url='/auth')

def view(request, message_id, template_name='usuario/mensajes/leer.html', mensaje=''):
    """
    Shows a single message.``message_id`` argument is required.
    The user is only allowed to see the message, if he is either 
    the sender or the recipient. If the user is not allowed a 404
    is raised. 
    If the user is the recipient and the message is unread 
    ``read_at`` is set to the current datetime.
    """
    user = request.user
    now = datetime.datetime.now()
    message = get_object_or_404(Message, id=message_id)
    esta_destinatario = False
    fecha_actual = datetime.datetime.today()

    if request.path.__contains__('previsualizar'):
        template_name = 'usuario/mensajes/previsualizar.html'

    destinatario = message.recipient
    if destinatario:
        if destinatario.grupos == None:
            if destinatario.usuarios.user == user:
                esta_destinatario = True
        elif destinatario.usuarios == None:
            if user in destinatario.grupos.user_set.all():
                esta_destinatario = True

    from django_messages.models import Destinatarios
    destin = Destinatarios.objects.get(usuarios__user=user)
    jefe = Destinatarios.objects.get(usuarios__user__userprofile__persona__cargo_principal__dependencia = message.sender.usuarios.user.profile.persona.cargo_principal.dependencia, usuarios__user__userprofile__persona__cargo_principal__cargo = message.sender.usuarios.user.profile.persona.cargo_principal.dependencia.cargo_max)

    # Si el usuario no esta entre los destinatarios, y el mensaje no lo envia el usuario y el usuario no es el jefe del que redacto el mensaje
    if not message.sender == destin and not esta_destinatario and not user == jefe.usuarios.user:
        raise Http404

    else:
        if message.status.nombre == 'Aprobado':
            message.read_at = now
            
            mensaje=message
            mensaje.save()
            mensaje_txt = "Mensaje nuevo leído."

            # Guardar log de memo archivado
            LogEntry.objects.create(
            user_id         = request.user.pk, 
            content_type_id = ContentType.objects.get_for_model(Message).id,
            object_id       = mensaje.id,
            object_repr     = repr(mensaje), 
            change_message  = mensaje_txt,
            action_flag     = CHANGE
            )

    return render(request, template_name, {
        'loggeado': request.user.is_authenticated,
        'request':request,
        'jefe':jefe,
        'fecha_actual':fecha_actual,
        'message': message,
    })
view = login_required(view, login_url='/auth')

def destin_atarios_lookup(request):
    # Default return list
    results = []
    if request.method == "GET":
        if 'query' in request.GET:
            value = request.GET['query']
            # Ignore queries shorter than length 3
            if len(value) > 2:
                model_results = Message.objects.filter(subject__istartswith=value)
                results = [ x.subject for x in model_results ]
                print(results)
    json = simplejson.dumps(results)
    return HttpResponse(json, content_type='application/json')

