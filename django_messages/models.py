# -*- coding: utf-8 -*-
import datetime
from django.db import models
from django.conf import settings
from django.db.models import signals
from django.db.models.query import QuerySet
from django.contrib.auth.models import User
from auth.models import Group
from auth.models import UserProfile
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError

class MessageManager(models.Manager):

    def inbox_for(self, user):
        """
        Returns all messages that were received by the given user and are not
        marked as deleted.
        """
        destinatarios = Destinatarios.objects.filter(models.Q(usuarios__user=user)|models.Q(grupos__user=user))
        return self.filter(
            recipient__in=destinatarios,
            deleted_at__isnull=True,
            status__nombre__iexact='Aprobado',
        )

    def trash_for(self, user):
        """
        Returns all messages that were either received or sent by the given
        user and are marked as deleted.
        """
        destinatarios = Destinatarios.objects.filter(models.Q(usuarios__user=user)|models.Q(grupos__user=user))
        filtro = self.filter(
            recipient__in=destinatarios,
            deleted_at__isnull=False,
        
        ) | self.filter(
            sender=destinatarios,
            recipient_deleted_at__isnull=False,
        )
        return filtro

class Destinatarios(models.Model):
    grupos = models.ForeignKey(Group, unique=True, null=True, blank=True)
    usuarios = models.ForeignKey(UserProfile, unique=True, null=True, blank=True)
    class Meta:
        db_table            = 'destinatarios'
        verbose_name_plural = 'destinatarios'
        verbose_name        = 'destinatario'
        ordering            = ['usuarios__persona__primer_nombre','usuarios__persona__primer_apellido','grupos__name']
    def __str__(self):
        if self.usuarios== None:
            return 'Grupo: %s'%(self.grupos)
        elif self.grupos == None:
            return '%s (%s de %s)'%(self.usuarios, self.usuarios.persona.cargo_principal.cargo.name, self.usuarios.persona.cargo_principal.dependencia.departamento)

class EstadoMemo(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    modificable = models.ManyToManyField(Group)
    def __str__(self):
        return '%s' %(self.nombre)

class Adjunto(models.Model):
    mensaje = models.ForeignKey('Message')
    archivo = models.FileField(upload_to='media/adjuntos/',null=True, blank=True)
    class Meta:
        db_table = 'adjuntos'
    def __str__(self):
        return '%s - %s' %(self.mensaje, self.archivo)

class Message(models.Model):
    """
    A private message from user to multiple users
    """
    recipient = models.ForeignKey('Destinatarios', related_name='received_messages', verbose_name=_("Destinatario"), null=True, blank=True)
    con_copia = models.BooleanField()
    subject = models.CharField(_("Subject"), max_length=255, null=True, blank=True)
    archivo = models.FileField(upload_to='media/adjuntos/',null=True, blank=True)
    body = models.TextField(verbose_name="Texto", null=True)
    sender = models.ForeignKey('Destinatarios', related_name='sent_messages', verbose_name=_("Sender"))
    parent_msg = models.ForeignKey('self', related_name='next_messages', null=True, blank=True, verbose_name=_("Parent message"))
    sent_at = models.DateTimeField(_("sent at"), null=True, blank=True)
    read_at = models.DateTimeField(_("read at"), null=True, blank=True)
    replied_at = models.DateTimeField(_("replied at"), null=True, blank=True)
    deleted_at = models.DateTimeField(("Archivado a las"), null=True, blank=True)
    status = models.ForeignKey('EstadoMemo', null=True, blank=True, verbose_name='Estado')
    tipo = models.CharField(max_length=10, blank=True, null=True)
    codigo = models.CharField(blank=True, null=True, verbose_name='código', max_length=30)
    num_ident= models.BigIntegerField(blank=True, null=True, verbose_name='número identificador')
    borrador = models.BooleanField()

    objects = MessageManager()

    '''
    def clean(self):
        for destin in self.recipient.get_query_set():
            if destin in self.con_copia.get_query_set():
                raise ValidationError(u'%s está como destinatario y con copia a la vez. Debe estar sólo en una de ambas listas.'%(destin))
    '''

    def new(self):
        """returns whether the recipient has read the message or not"""
        if self.read_at is not None:
            return False
        return True
        
    def replied(self):
        """returns whether the recipient has written a reply to this message"""
        if self.replied_at is not None:
            return True
        return False
    
    def __str__(self):
        return self.subject
    
    def get_por_aprobar_url(self):
        return ('ver_por_aprobar', [self.id])
    get_por_aprobar_url = models.permalink(get_por_aprobar_url)
    
    def get_absolute_url(self):
        return ('messages_detail', [self.id])
    get_absolute_url = models.permalink(get_absolute_url)
    
    class Meta:
        ordering = ['-sent_at']
        verbose_name = _("Message")
        verbose_name_plural = _("Messages")

@receiver(pre_save, sender=Message)
def save_message(sender, **kwargs):
    from django.contrib.auth.models import User
    from auth.models import UserProfile
    from django_messages.models import EstadoMemo
    memo = kwargs['instance']
    if memo.status == None:
        estado = EstadoMemo.objects.get(nombre='En espera')
        memo.status=estado
    if memo.sent_at == None:
        memo.sent_at = datetime.datetime.now()

def inbox_count_for(user):
    """
    returns the number of unread messages for the given user but does not
    mark them seen
    """
    return Message.objects.filter(recipient=user, read_at__isnull=True, recipient_deleted_at__isnull=True).count()

# fallback for email notification if django-notification could not be found
if "notification" not in settings.INSTALLED_APPS:
    from django_messages.utils import new_message_email
    signals.post_save.connect(new_message_email, sender=Message)
