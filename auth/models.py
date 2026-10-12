# -*- coding: utf8
from django.db import models
from django.contrib.auth.models import User, UserManager, Permission, GroupManager
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext, ugettext_lazy as _
#User.add_to_class('sede', models.ForeignKey(Sedes,null=True))
from django.core.validators import MaxLengthValidator #Clase para establecer la cantidad de caracteres del username del admin

NEW_USERNAME_LENGTH = 250 # Variable de tamaño

def username_largo():
    ''' Función para establecer el tamaño del campo username del modelo User de Django que por defecto es de 30 y por la validación no dejaba editar en el admin los usuarios con mas de 30 caracteres '''
    username = User._meta.get_field("username")
    username.max_length = NEW_USERNAME_LENGTH
    for v in username.validators:
        if isinstance(v, MaxLengthValidator):
            v.limit_value = NEW_USERNAME_LENGTH

username_largo() # Llamado a la función la cual debe ser antes de cargar la app django.contrib.auth

class Group(models.Model):
    name = models.CharField(_('name'), max_length=80, unique=True)
    permissions = models.ManyToManyField(Permission,
        verbose_name=_('permissions'), blank=True)

    objects = GroupManager()

    class Meta:
        verbose_name = _('group')
        verbose_name_plural = _('groups')

    def __str__(self):
        return '%s' %(self.name)

    def natural_key(self):
        return (self.name,)

class Pregunta(models.Model):
    opcion = models.CharField(max_length=50, verbose_name='opción')

    def __str__(self):
        return '%s' %(self.opcion)

class PreguntasSecretas(models.Model):
    pregunta = models.ForeignKey('Pregunta')
    respuesta = models.CharField(max_length=300)
    usuario = models.ForeignKey(User)
    class Meta:
        verbose_name = 'Pregunta secreta'
        verbose_name_plural = 'Preguntas secretas'
    def __str__(self):
        return '%s' %(self.pregunta)

class UserProfile(models.Model):
    from personas.models import Personas
    user=models.ForeignKey(User)
    persona=models.OneToOneField(Personas,null=False,help_text='Por favor, ingrese nombre, apellido o cédula de la persona')
    notificaciones=models.BooleanField(default=False,help_text='Active esta casilla si desea el envío de notificaciones a su correo electrónico')

    class Meta:
        verbose_name='Usuario'
        unique_together=('user','persona')

    def __str__(self):
        return '%s %s' %(self.persona.primer_nombre, self.persona.primer_apellido)

    def natural_key(self):
        return '%s (%s)' %(self.persona.natural_key(),self.user.__unicode__() )

def funcion(u):
    if not hasattr(u, '_cached_profile'):
        u._cached_profile = UserProfile.objects.get_or_create(user=u)[0]
    return u._cached_profile 
User.profile = property(funcion)

@receiver(post_save, sender=Group)
def save_group_dest(sender, **kwargs):
    ''' Guardar en la tabla Destinatarios el grupo a crear '''
    from django_messages.models import Destinatarios
    destinatario = Destinatarios.objects.get_or_create(grupos=kwargs['instance'])
    '''
    grupo = Group.objects.get_or_create(name = 'Todos')
    grupo = Group.objects.get_or_create(name = 'Nadie')
    '''

@receiver(post_save, sender='UserProfile')
def save_user_dest(sender, **kwargs):
    ''' Guardar en la tabla Destinatarios el usuario creado '''
    from django_messages.models import Destinatarios
    destinatario = Destinatarios.objects.get_or_create(usuarios=kwargs['instance'])

