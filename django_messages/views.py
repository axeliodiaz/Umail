# -*- coding: utf-8 -*-
import datetime
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_noop
from django.core.urlresolvers import reverse
from django.conf import settings

from django_messages.models import Message
from django_messages.forms import ComposeForm
from django_messages.utils import format_quote

if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification
else:
    notification = None

def inbox(request, mensaje=''):
    """
    Displays a list of received messages for the current user.
    Optional Arguments:
        ``template_name``: name of the template to use.
    """
    notify = False
    if not mensaje == '':
        notify = True
    if request.user.is_authenticated():
        message_list = Message.objects.inbox_for(request.user).distinct()
        if not message_list.exists():
            mensaje = u'No tiene ningún mensaje hasta ahora'
        return render_to_response('user/mensajes/inbox.html', {
            'message_list': message_list,
            'loggeado': request.user.is_authenticated,
            'request':request,
            'mensaje':mensaje,
            'notify':notify,
        }, context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect('/')

def outbox(request, template_name='django_messages/outbox.html'):
    """
    Displays a list of sent messages by the current user.
    Optional arguments:
        ``template_name``: name of the template to use.
    """
    message_list = Message.objects.outbox_for(request.user)
    return render_to_response(template_name, {
        'message_list': message_list,
    }, context_instance=RequestContext(request))
outbox = login_required(outbox)

def trash(request, template_name='user/mensajes/papelera.html'):
    """
    Displays a list of deleted messages. 
    Optional arguments:
        ``template_name``: name of the template to use
    Hint: A Cron-Job could periodicly clean up old messages, which are deleted
    by sender and recipient.
    """
    message_list = Message.objects.trash_for(request.user)
    return render_to_response(template_name, {
        'message_list': message_list,
        'loggeado': request.user.is_authenticated,
        'request':request,
    }, context_instance=RequestContext(request))
trash = login_required(trash)

def compose(request, recipient=None,
        template_name='user/mensajes/redactar.html', success_url=None, recipient_filter=None):
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
    if request.method == "POST":
        form = ComposeForm(request.POST)
        if form.is_valid():
            from django_messages.models import Destinatarios, EstadoMemo
            estado_memo = EstadoMemo.objects.get(nombre='En espera')
            #form = form_class(request.POST)
            #form = form_class(request.POST, recipient_filter=recipient_filter)
            mensaje = Message(
                            sender = Destinatarios.objects.get(usuarios__user=request.user),
                            subject = request.POST['subject'],
                            body = request.POST['body'],
                            status = estado_memo,
                            tipo = '',
                        )
            mensaje.save()
            for destin in request.POST['recipient']:
                try:
                    sender = Destinatarios.objects.filter(id=destin)
                except:
                    continue
                else:
                    sender = Destinatarios.objects.filter(id=destin)
                    mensaje.recipient.add(sender[0])
            #messages.info(request, _(u"Message successfully sent."))
            mensaje = u'Mensaje enviado satisfactoriamente'
            return inbox(request, mensaje)
            if success_url is None:
                success_url = reverse('messages_inbox')
            if request.GET.has_key('next'):
                success_url = request.GET['next']
            return HttpResponseRedirect(success_url)
    else:
        form = ComposeForm()
        form.fields['body'].initial = "\n\n\n\n\n\n\n\nCordialmente, \n%s %s" %(request.user.profile.persona, request.user.profile.persona.cargo_principal.cargo)
        if recipient is not None:
            recipients = [u for u in User.objects.filter(username__in=[r.strip() for r in recipient.split('+')])]
            form.fields['recipient'].initial = recipients
    return render_to_response(template_name, {
        'loggeado': request.user.is_authenticated,
        'request':request,
        'form': form,
    }, context_instance=RequestContext(request))
compose = login_required(compose)

def reply(request, message_id, form_class=ComposeForm,
        template_name='django_messages/compose.html', success_url=None, 
        recipient_filter=None, quote_helper=format_quote):
    """
    Prepares the ``form_class`` form for writing a reply to a given message
    (specified via ``message_id``). Uses the ``format_quote`` helper from
    ``messages.utils`` to pre-format the quote. To change the quote format
    assign a different ``quote_helper`` kwarg in your url-conf.
    
    """
    parent = get_object_or_404(Message, id=message_id)
    
    if parent.sender != request.user and parent.recipient != request.user:
        raise Http404
    
    if request.method == "POST":
        sender = request.user
        form = form_class(request.POST, recipient_filter=recipient_filter)
        if form.is_valid():
            form.save(sender=request.user, parent_msg=parent)
            messages.info(request, _(u"Message successfully sent."))
            if success_url is None:
                success_url = reverse('messages_inbox')
            return HttpResponseRedirect(success_url)
    else:
        form = form_class(initial={
            'body': quote_helper(parent.sender, parent.body),
            'subject': _(u"Re: %(subject)s") % {'subject': parent.subject},
            'recipient': [parent.sender,]
            })
    return render_to_response(template_name, {
        'form': form,
    }, context_instance=RequestContext(request))
reply = login_required(reply)

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
    if request.GET.has_key('next'):
        success_url = request.GET['next']
    if message.sender.usuarios.user == user:
        message.sender_deleted_at = now
        deleted = True
    for destinatario in message.recipient.get_query_set():
        if destinatario.grupos == None:
            if destinatario.usuarios.user.username == user.username:
                message.recipient_deleted_at = now
                deleted = True
        elif destinatario.usuarios == None:
            if user in destinatario.grupos.user_set.get_query_set():
                message.recipient_deleted_at = now
                deleted = True
    if deleted:
        message.save()
        notify = True
        #messages.info(request, _(u"Message successfully deleted."))
        if notification:
            notification.send([user], "messages_deleted", {'message': message,})
        mensaje = u'¡Mensaje eliminado satisfactoriamente!'
        return inbox(request, mensaje)
    raise Http404
delete = login_required(delete)

def undelete(request, message_id, success_url=None):
    """
    Recovers a message from trash. This is achieved by removing the
    ``(sender|recipient)_deleted_at`` from the model.
    """
    user = request.user
    message = get_object_or_404(Message, id=message_id)
    undeleted = False
    if success_url is None:
        success_url = reverse('messages_inbox')
    if request.GET.has_key('next'):
        success_url = request.GET['next']
    if message.sender == user:
        message.sender_deleted_at = None
        undeleted = True
    if message.recipient == user:
        message.recipient_deleted_at = None
        undeleted = True
    if undeleted:
        message.save()
        messages.info(request, _(u"Message successfully recovered."))
        if notification:
            notification.send([user], "messages_recovered", {'message': message,})
        return HttpResponseRedirect(success_url)
    raise Http404
undelete = login_required(undelete)

def view(request, message_id, template_name='user/mensajes/leer.html'):
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

    for destinatario in message.con_copia.get_query_set():
        if destinatario.grupos == None:
            if destinatario.usuarios.user == user:
                esta_destinatario = True
                continue
        elif destinatario.usuarios == None:
            if user in destinatario.grupos.user_set.get_query_set():
                esta_destinatario = True
                continue

    for destinatario in message.recipient.get_query_set():
        if destinatario.grupos == None:
            if destinatario.usuarios.user == user:
                esta_destinatario = True
                continue
        elif destinatario.usuarios == None:
            if user in destinatario.grupos.user_set.get_query_set():
                esta_destinatario = True
                continue

    if (message.sender != user) and (esta_destinatario == False):
        raise Http404

    if message.read_at is None and esta_destinatario == True:
        message.read_at = now
        from django_messages.models import Destinatarios
        
        message.leido_por.add(Destinatarios.objects.get(usuarios__user=user))
        message.save()
    return render_to_response(template_name, {
        'loggeado': request.user.is_authenticated,
        'request':request,
        'message': message,
    }, context_instance=RequestContext(request))
view = login_required(view)
