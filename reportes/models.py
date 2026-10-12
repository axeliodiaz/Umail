# -*- coding: utf8 -*-
from django.db import models

# Create your models here.
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from auth.models import UserProfile

class Comentarios(models.Model):
    pregunta = models.CharField(max_length=50, verbose_name='título')
    comentario = models.TextField()
    nombre = models.CharField(max_length=50, verbose_name="nombre y apellido")
    correo = models.EmailField()
    archivo = models.FileField(upload_to='media/adjuntos/',null=True, blank=True)
    class Meta:
        db_table            = 'comentarios'
        verbose_name_plural = 'comentarios'
    def __str__(self):
        return '%s: %s'%(self.correo, self.pregunta)

class Respuestas(models.Model):
    pregunta = models.ForeignKey('Comentarios', editable=False)
    comentario = models.TextField()
    usuario = models.ForeignKey(UserProfile, null=True, blank=True, editable=False)
    respondido = models.BooleanField(default=False, editable=False)
    class Meta:
        db_table            = 'respuestas'
        verbose_name_plural = 'respuestas'
    def __str__(self):
        return '%s'%(self.pregunta)

@receiver(post_save, sender=Respuestas)
def save_response(sender, **kwargs):
    from lib.umail import enviar_email

    respuesta = kwargs['instance']
    if respuesta.respondido == False:
        respuesta.respondido = True

    # Enviar correo de respuesta
    asunto = 'Respuesta a "%s"'%(respuesta.pregunta.pregunta)
    contenido = 'Uno de nuestros administradores ha respondido a su pregunta "%s" con el siguiente contenido: \n\n%s' %(respuesta.pregunta.pregunta, respuesta.comentario)
    enviar_email(asunto=asunto, contenido=contenido, correos=(respuesta.pregunta.correo,))
