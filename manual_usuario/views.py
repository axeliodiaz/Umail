# -*- coding: utf-8 -*-
from manual_usuario.models import *
from django.views.generic.base import View
from lib.umail import msj_expresion, renderizar_plantilla
from django.shortcuts import render_to_response, get_object_or_404
'''
admin.site.register(Modulo)
'''

class Manual(View):
    template = 'usuario/manual/principal.html'

    def get(self, request, *args, **kwargs):
        import pdb
        #pdb.set_trace()
        context = {}
        seccion = ''
        mostrar_todos = False
        if 'manual_id' in kwargs:
            seccion_id = kwargs['manual_id']
            modulos = SubModulo.objects.filter(modulo__id=seccion_id)
            if not modulos.exists():
                mostrar_todos = True
        else:
            mostrar_todos = True

        if mostrar_todos:
            modulos = Modulo.objects.all()
        context.update({'modulos':modulos.order_by('id')})
        context.update({'request':request})
        return render_to_response(self.template, context)
