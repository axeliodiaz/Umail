# -*- coding: utf8
from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext, gettext_lazy as _
#User.add_to_class('sede', models.ForeignKey(Sedes,null=True, on_delete=models.CASCADE))

class Pregunta(models.Model):
    opcion = models.CharField(max_length=50, verbose_name='opción')

    def __str__(self):
        return '%s' %(self.opcion)

class PreguntasSecretas(models.Model):
    pregunta = models.ForeignKey('Pregunta', on_delete=models.CASCADE)
    respuesta = models.CharField(max_length=300)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    class Meta:
        verbose_name = 'Pregunta secreta'
        verbose_name_plural = 'Preguntas secretas'
    def __str__(self):
        return '%s' %(self.pregunta)

class UserProfile(models.Model):
    from personas.models import Personas
    user=models.ForeignKey(User, on_delete=models.CASCADE)
    persona=models.OneToOneField(Personas,null=False,help_text='Por favor, ingrese nombre, apellido o cédula de la persona', on_delete=models.CASCADE)
    notificaciones=models.BooleanField(default=False,help_text='Active esta casilla si desea el envío de notificaciones a su correo electrónico')

    class Meta:
        verbose_name='Usuario'
        unique_together=('user','persona')

    def __str__(self):
        return '%s %s' %(self.persona.primer_nombre, self.persona.primer_apellido)

    def natural_key(self):
        return '%s (%s)' %(self.persona.natural_key(),str(self.user) )

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

@receiver(post_save, sender=UserProfile)
def save_user_dest(sender, **kwargs):
    ''' Guardar en la tabla Destinatarios el usuario creado '''
    from django_messages.models import Destinatarios
    destinatario = Destinatarios.objects.get_or_create(usuarios=kwargs['instance'])

