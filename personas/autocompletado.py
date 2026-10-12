# -*- coding: utf8
from personas.models import *
from django.db.models import Q

'''Autocompletado para Estudiantes'''
class PersonasLookup(Personas):
    def get_query(self,q,request):
        return Personas.objects.filter(Q(num_identificacion__icontains=q) | Q(primer_nombre__icontains=q) | Q(primer_apellido__icontains=q) | Q(email__icontains=q))

    def format_result(self,personas):
        return '%s - %s %s' % (personas.num_identificacion, personas.primer_nombre, personas.primer_apellido)

    def format_item(self,Personas):
        return str(Personas)

    def get_objects(self,ids):
        return Personas.objects.filter(pk__in=ids).order_by('num_identificacion','primer_nombre','primer_apellido')
