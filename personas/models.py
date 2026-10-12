# -*- coding: utf8 -*-
from django.db import models
from sedes.models import Niveles, Dependencias
from django.dispatch import receiver
from django.db.models.signals import post_save

# Modelo para aplicación de personas
class Personas(models.Model):
    tipodoc                 = models.CharField(choices=(('c','Cédula'),('p','Pasaporte')),default=0,max_length=1, verbose_name='Tipo de Identificación')
    num_identificacion      = models.CharField(max_length=50,unique=True,verbose_name='Número de Identificación')
    primer_apellido         = models.CharField(max_length=100)
    segundo_apellido        = models.CharField(max_length=100,blank=True)
    primer_nombre           = models.CharField(max_length=100)
    segundo_nombre          = models.CharField(max_length=100,blank=True)
    genero                  = models.IntegerField(choices=((0,'Masculino'),(1,'Femenino')),default=0,verbose_name='género')
    email                   = models.EmailField()
    telefono                = models.CharField(max_length=15, null=True, blank=True, verbose_name='teléfono', help_text='Por favor, incluya el código de telefonía o área.')
    cargo_principal         = models.ForeignKey('Personal',related_name='cargo_principal')
    cargos_autorizados      = models.ManyToManyField('Personal', null=True, blank=True, default=None, related_name='cargos_autorizados')
    class Meta:
        db_table            = 'personas'
        verbose_name_plural = 'personas'
    def __str__(self):
        return '%s %s'%(self.primer_nombre,self.primer_apellido)
    def natural_key(self):
        return '%s %s'%(self.primer_nombre,self.primer_apellido)

@receiver(post_save, sender=Personas)
def save_pers_user(sender, **kwargs):
    ''' Guardar en la tabla Destinatarios el usuario creado '''
    from django.contrib.auth.models import User
    from auth.models import UserProfile
    from django_messages.models import Destinatarios
    persona = kwargs['instance']
    usuario = User.objects.filter(models.Q(username=persona.email)|models.Q(email=persona.email))
    usuario_perfil = UserProfile.objects.filter(user=usuario)
    if not usuario.exists():
        usuario = User.objects.create_user(username = persona.email, email = persona.email, password = persona.num_identificacion)
        if not usuario_perfil.exists():
            usuario_perfil = UserProfile.objects.create(persona=persona, user=usuario)
        else:
            usuario_perfil = usuario_perfil[0]
    else:
        usuario = usuario[0]
        if not usuario_perfil.exists():
            usuario_perfil = UserProfile.objects.create(persona=persona, user=usuario)
        else:
            usuario_perfil = usuario_perfil[0]

    # Guardar al usuario en el grupo donde desempeñe el cargo principal
    usuario.groups.add(persona.cargo_principal.id)

    usuario.first_name = persona.primer_nombre
    usuario.last_name = persona.primer_apellido
    usuario.is_staff = True
    usuario.save()
    destinatario = Destinatarios.objects.get_or_create(usuarios=usuario_perfil)


class Personal(models.Model):
    from auth.models import Group
    tipo_personal           = models.ForeignKey('TipoPersonal')
    dependencia             = models.ForeignKey(Dependencias)
    cargo                   = models.ForeignKey(Group,related_name='cargo_principal')
    class Meta:
        db_table = 'personal'
        verbose_name_plural = 'personal'
    def __str__(self):
        return '%s de %s' %(self.cargo, self.dependencia)


class TipoPersonal(models.Model):
    nombre                  = models.CharField(max_length=50)
    class Meta:
        db_table            = 'tipo_personal'
        verbose_name_plural = 'tipos de personal'
        verbose_name        = 'tipo de personal'
    def __str__(self):
        return '%s' %(self.nombre)
