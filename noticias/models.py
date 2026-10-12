#-*- coding: UTF8 -*-
from django.db import models

# Create your models here.
class Noticias(models.Model):
    titulo = models.CharField(max_length=300, verbose_name='título')
    texto = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table            = 'noticias'
        verbose_name_plural = 'noticias'
        verbose_name        = 'noticias'
    def __str__(self):
        return '%s - %s' %(self.titulo, self.texto)
