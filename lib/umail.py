# -*- coding: utf-8 -*-
from django.shortcuts import render

def msj_expresion(tipo_mensaje):
    '''
    Función que permite el establecimiento de los mensajes
    para el front-end siguiendo configuraciones de Bootstrap
    '''
    expresion = ''
    if tipo_mensaje == 'alert':
        expresion = u'¡Atención! '
    if tipo_mensaje == 'success':
        expresion = u'¡Genial! '
    if tipo_mensaje == 'error':
        expresion = u'¡ERROR! '
    if tipo_mensaje == 'Information':
        expresion = u'¿Sabías qué? '
    return (tipo_mensaje, expresion)


def renderizar_plantilla(request, plantilla, tipo_mensaje='', expresion='', mensaje='', form='', extra=''):
    '''
    Función personalizada para Umail y la renderización de plantillas 
    con mensajes pasando por estilos de Bootstrap
    '''
    diccionario = {}

    # Actualización de los mensajes para el formulario
    diccionario.update({'tipo_mensaje': tipo_mensaje, 'expresion': expresion, 'mensaje': mensaje})

    # Actualización del CSRF
    from django.core.context_processors import csrf
    diccionario.update(csrf(request))

    # Actualización del formulario
    diccionario.update({'formulario':form})
    num_ext = 0
    for ext in extra:
        num_ext = num_ext + 1
        diccionario.update({'extra_%s'%(num_ext):ext})
    return render(request, plantilla, diccionario)
