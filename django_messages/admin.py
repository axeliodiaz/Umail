# -*- coding: utf-8 -*-
from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django_summernote.widgets import SummernoteWidget

if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification
else:
    notification = None
    
from django_messages.models import Message, Destinatarios, Adjunto, EstadoMemo

class AdjuntosInline(admin.TabularInline):
    model = Adjunto
    extra = 1

class MessageAdminForm(forms.ModelForm):
    """
    Custom AdminForm to enable messages to groups and all users.
    """
    '''
    group = forms.ChoiceField(label=_('group'), required=False,
        help_text=_('Creates the message optionally for all users or a group of users.'))

    def __init__(self, *args, **kwargs):
        super(MessageAdminForm, self).__init__(*args, **kwargs)
        self.fields['group'].choices = self._get_group_choices()

    def _get_group_choices(self):
        return [('', u'---------'), ('all', _('All users'))] + \
            [(group.pk, group.name) for group in Group.objects.all()]
    '''

    class Meta:
        model = Message
        fields = '__all__'
        widgets = {
                    'body': SummernoteWidget()
                }

    def clean(self):
        destinatarios = self.cleaned_data['recipient']
        # --- Tipo --- #
        '''
        if destinatarios.__len__() > 1:
            self.cleaned_data['tipo'] = u'Circular'
        else:
            destin = Destinatarios.objects.get(id=destinatarios[0])
            # Si el grupo está vacío entonces es a un solo usuario
            if destin.grupos == None:
                self.cleaned_data['tipo'] = u'Personal'
            elif destin.grupos.user_set.all().count() > 1:
                self.cleaned_data['tipo'] = u'Circular'
            else:
                self.cleaned_data['tipo'] = u'Personal'
        # --- Destinatarios --- #
        # Revisar si está el grupo Todos en destinatarios
        todos = Destinatarios.objects.get(grupos__name__iexact='Todos')
        if todos.id in (self.cleaned_data['recipient']):
            self.cleaned_data['recipient'].__init__()
            self.cleaned_data['recipient'].append(todos.id)
        else:
            usuarios_dest = []
            grupos_dest = []
            usuarios = []
            grupos = []
            dest_final = []
            for destinatario in self.cleaned_data['recipient']:
                dest = Destinatarios.objects.get(id=destinatario)
                # Si el destinatario NO es un grupo:
                if dest.grupos == None:
                    usuarios.append(dest.usuarios)
                    usuarios_dest.append(dest)
                else:
                    grupos.append(dest.grupos)
                    grupos_dest.append(dest)

            # Revisar que los usuarios no se encuentren en un grupo ya listado
            for usuario in usuarios_dest:
                if usuario.usuarios.user.groups.all().filter(id__in=self.cleaned_data['recipient']).exists():
                    self.cleaned_data['recipient'].remove(usuario.id)

        # --- Con Copia --- #
        todos = Destinatarios.objects.get(grupos__name__iexact='Todos')
        destinatarios = self.cleaned_data['con_copia']
        if todos.id in (self.cleaned_data['con_copia']):
            self.cleaned_data['con_copia'].__init__()
            self.cleaned_data['con_copia'].append(todos.id)
        else:
            usuarios_dest = []
            grupos_dest = []
            usuarios = []
            grupos = []
            dest_final = []
            for destinatario in self.cleaned_data['con_copia']:
                dest = Destinatarios.objects.get(id=destinatario)
                # Si el destinatario NO es un grupo:
                if dest.grupos == None:
                    usuarios.append(dest.usuarios)
                    usuarios_dest.append(dest)
                else:
                    grupos.append(dest.grupos)
                    grupos_dest.append(dest)

            # Revisar que los usuarios no se encuentren en un grupo ya listado
            for usuario in usuarios_dest:
                if usuario.usuarios.user.groups.all().filter(id__in=self.cleaned_data['con_copia']).exists():
                    self.cleaned_data['con_copia'].remove(usuario.id)

        '''
        return self.cleaned_data

from django_messages.forms import ComposeForm
class MessageAdmin(admin.ModelAdmin):
    form = MessageAdminForm
    list_display = ('subject', 'sender', 'recipient', 'sent_at', 'read_at', 'status', 'con_copia')
    list_filter = ('sent_at', 'sender', 'tipo')
    search_fields = ('subject', 'body', 'codigo')

    def save_model(self, request, obj, form, change):
        """
        Saves the message for the recipient and looks in the form instance
        for other possible recipients. Prevents duplication by excludin the
        original recipient from the list of optional recipients.

        When changing an existing message and choosing optional recipients,
        the message is effectively resent to those users.
        """
        
        #@TODO: Revisar la funcionalidad del envío de mensajes por correo electrónico
        if notification:
            # Getting the appropriate notice labels for the sender and recipients.
            if obj.parent_msg is None:
                sender_label = 'messages_sent'
                recipients_label = 'messages_received'
            else:
                sender_label = 'messages_replied'
                recipients_label = 'messages_reply_received'
                
            # Notification for the sender.
            notification.send([obj.sender], sender_label, {'message': obj,})

        '''
        # Si está asignado 'todos' los usuarios (grupo Todos)
        dest_grupos = Destinatarios.objects.filter(grupos__in=form.cleaned_data['recipient'])
        revisar_usuarios = True
        destinatarios = form.cleaned_data['recipient']

        if dest_grupos.filter(grupos__name__iexact='Todos').exists():
            destin = Destinatarios.objects.get(grupos__name__iexact='Todos')
            revisar_usuarios = False
            destinatarios = obj.recipient
            for dest in destinatarios.all():
                # Cualquier grupo que no sea 'Todos' debe eliminarse de los destinatarios
                if not dest.id == destin.id:
                    obj.recipient.remove(dest)
                else:
                    obj.recipient.add(dest)

            recipientes = [str(r[0]) for r in obj.recipient.all().values_list('id')]
            destinatarios = form.cleaned_data['recipient']
            request.POST['recipient'] = '|'.join(recipientes)
            obj.save()

        if revisar_usuarios:
            dest_user = Destinatarios.objects.filter(grupos__in=form.cleaned_data['recipient'])
            for dest in dest_user :
                obj.recipient.add(dest)
                '''
        obj.save()

        '''
        if form.cleaned_data['group'] == 'all':
            # send to all users
            recipients = User.objects.exclude(pk=obj.recipient.pk)
        else:
            # send to a group of users
            recipients = []
            group = form.cleaned_data['group']
            if group:
                group = Group.objects.get(pk=group)
                recipients.extend(
                    list(group.user_set.exclude(pk=obj.recipient.pk)))
        # create messages for all found recipients
        for user in recipients:
            obj.pk = None
            obj.recipient = user
            obj.save()

            if notification:
                # Notification for the recipient.
                notification.send([user], recipients_label, {'message' : obj,})
        '''
#admin.site.register(Message, MessageAdmin)

class MensajeAdmin(admin.ModelAdmin):
    form = ComposeForm
#admin.site.register(Message, MensajeAdmin)
#admin.site.register(EstadoMemo)
#admin.site.register(Destinatarios)
