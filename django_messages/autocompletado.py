# -*- coding: utf8
from django.db.models import Q
from auth.models import UserProfile
from django_messages.models import Destinatarios

'''Autocompletado para Estudiantes'''
class UserLookup(UserProfile):
    def get_query(self,q,request):
        return UserProfile.objects.filter(Q(user__username__icontains=q) | Q(persona__num_identificacion__icontains=q) | Q(persona__primer_nombre__icontains=q) | Q(persona__primer_apellido__icontains=q) | Q(persona__email__icontains=q))

    def format_result(self,userprofile):
        return '%s - %s %s' % (userprofile.persona.num_identificacion, userprofile.persona.primer_nombre, userprofile.persona.primer_apellido)

    def format_item(self,UserProfile):
        return str(UserProfile)

    def get_objects(self,ids):
        return UserProfile.objects.filter(pk__in=ids).order_by('persona__num_identificacion','persona__primer_nombre','persona__primer_apellido')

'''Autocompletado para Estudiantes'''
class DestinatariosLookup(Destinatarios):
    def get_query(self,q,request):
        return Destinatarios.objects.filter(Q(usuarios__user__username__icontains=q) | Q(usuarios__persona__num_identificacion__icontains=q) | Q(usuarios__persona__primer_nombre__icontains=q) | Q(usuarios__persona__primer_apellido__icontains=q) | Q(grupos__name__icontains=q))

    def format_result(self,destinatarios):
        if not destinatarios.usuarios == None:
            return '%s' % (destinatarios.usuarios.persona)
        elif not destinatarios.grupos == None:
            return '%s' % (destinatarios.grupos.name)

    def format_item(self,Destinatarios):
        return str(Destinatarios)

    def get_objects(self,ids):
        return Destinatarios.objects.filter(pk__in=ids).order_by('usuarios__persona__num_identificacion','usuarios__persona__primer_nombre','usuarios__persona__primer_apellido','grupos__name')
