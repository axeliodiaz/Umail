# -*- coding: utf8 -*-
# Create your views here.
from noticias.models import *
from django.contrib.auth.decorators import login_required
from django.template.context_processors import csrf
from django.shortcuts import render

@login_required
def todas_noticias(request):
    diccionario = {}
    diccionario.update(csrf(request))
    noticias = Noticias.objects.all()
    diccionario.update({'request':request})
    diccionario.update({'noticias':noticias})
    diccionario.update({'loggeado':request.user.is_authenticated})
    return render(request, 'user/noticias/todas.html', diccionario)

@login_required
def detalle_noticia(request, noticia_id):
    diccionario = {}
    diccionario.update(csrf(request))
    noticias = Noticias.objects.filter(id=noticia_id)
    diccionario.update({'request':request})
    diccionario.update({'noticia_exists':noticias.exists()})
    diccionario.update({'loggeado':request.user.is_authenticated})
    if noticias.exists():
        diccionario.update({'noticia':noticias[0]})
    return render(request, 'user/noticias/especificas.html', diccionario)

