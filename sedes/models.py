# -*- coding: utf-8 -*-
from django.db import models
from auth.models import Group

# Modelo para la aplicación de sedes
class Dependencias(models.Model):
    ubicacion               = models.ForeignKey('Parroquias', help_text='Escriba y seleccione una parroquia', verbose_name='ubicación', on_delete=models.CASCADE)
    tipo_sede               = models.ForeignKey('TipoSede', on_delete=models.CASCADE)
    departamento            = models.CharField(max_length=50, verbose_name='nombre del departamento')
    siglas                  = models.CharField(max_length=50, verbose_name='iniciales del departamento')
    telefono                = models.IntegerField(unique=True, null=True, blank=True, help_text='Por favor, incluya el código de telefonía o área.', verbose_name='teléfono')
    nivel                   = models.ForeignKey('Niveles', on_delete=models.CASCADE)
    dependencia             = models.ForeignKey('self', null=True, blank=True, verbose_name='dependencia superior', on_delete=models.CASCADE)
    cargo_max               = models.ForeignKey(Group, help_text='Superior máximo de la dependencia. Firmante de los memorándums', null=True, blank=True, on_delete=models.CASCADE)
    class Meta:
        db_table            = 'dependencias'
        verbose_name_plural = 'dependencias'
        verbose_name      = 'dependencia'
    def __str__(self):
        return '(%s) %s' %(self.siglas, self.departamento)

class TipoSede(models.Model):
    nombre                  = models.CharField(max_length=20)
    class Meta:
        db_table            = 'tipo_sede'
        verbose_name_plural = 'tipo de sedes'
        verbose_name      = 'tipo de sede'
    def __str__(self):
        return '%s' %(self.nombre)

class Niveles(models.Model):
    numero                  = models.IntegerField(verbose_name = 'número', unique=True)
    class Meta:
        db_table            = 'niveles'
        verbose_name_plural = 'niveles'
        verbose_name        = 'nivel'
    def __str__(self):
        return '%s' %(self.numero)

class Parroquias(models.Model):
    nombre                  = models.CharField(max_length=100,)
    municipio               = models.ForeignKey('Municipio', on_delete=models.CASCADE)
    class Meta:
        db_table            = 'parroquia'
        verbose_name_plural = 'parroquias'
        verbose_name        = 'parroquia'
    def __str__(self):
        return self.nombre

class Municipio(models.Model):
    nombre                  = models.CharField(max_length=100)
    estado                  = models.ForeignKey('Estado', on_delete=models.CASCADE)
    class Meta:
        db_table            = 'municipio'
        verbose_name_plural = 'municipios'
        verbose_name        = 'municipio'
    def __str__(self):
        return self.nombre

class Estado(models.Model):
    nombre                  = models.CharField(max_length=100)
    pais                    = models.ForeignKey('Pais',verbose_name='país', on_delete=models.CASCADE)
    class Meta:
        db_table            = 'estado'
        verbose_name_plural = 'estados'
    def __str__(self):
        return '%s'%(self.nombre)

class Pais(models.Model):
    nombre                  = models.CharField(max_length=50)
    class Meta:
        db_table            = 'pais'
        #verbose_name_plural = 'paises'
        verbose_name_plural = 'países'
        verbose_name        = 'país'
    def __str__(self):
        return "%s" % (self.nombre)


