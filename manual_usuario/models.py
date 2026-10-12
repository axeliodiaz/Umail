# -*- coding: utf8 -*-
from django.db import models
from sedes.models import Niveles, Dependencias
from django.dispatch import receiver
from django.db.models.signals import post_save

ALINEADO = (('Derecha','Derecha'),('Izquierda','Izquierda'))
class Modulo(models.Model):
    titulo = models.CharField(max_length=100, verbose_name='título',)
    alineacion = models.CharField(max_length=10,choices=ALINEADO, default='', verbose_name='alineación')
    imagen = models.ImageField(upload_to='manual/',null=True, blank=True)
    resumen = models.TextField()
    class Meta:
        db_table            = 'modulo'
        verbose_name        = 'módulo'
    def __str__(self):
        return '%s' %(self.titulo)

class SubModulo(models.Model):
    modulo = models.ForeignKey('Modulo', verbose_name='módulo', on_delete=models.CASCADE)
    titulo = models.CharField(max_length=100, verbose_name='título')
    alineacion = models.CharField(max_length=10,choices=ALINEADO, default='', verbose_name='alineación')
    imagen = models.ImageField(upload_to='manual/',null=True, blank=True)
    resumen = models.TextField()
    class Meta:
        db_table            = 'submodulo'
        verbose_name        = 'submódulo'
    def __str__(self):
        return '%s' %(self.titulo)
