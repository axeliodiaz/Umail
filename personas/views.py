# -*- coding: utf-8 -*-
import random
from django.contrib.auth.decorators import login_required
from personas.forms import PerfilForm, FiltroForm
from django.http import Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.models import User
from django.template import RequestContext
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.views.decorators.csrf import csrf_protect
from django.core.context_processors import csrf
from django import forms
from django.http import HttpResponseRedirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import models
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.formtools.wizard.views import SessionWizardView
from django.views.generic.base import View
from django.forms.formsets import formset_factory
from personas.forms import PreguntasForm
from django.forms.models import modelformset_factory
from django.forms import TextInput
from django.contrib.auth import login
from lib.umail import msj_expresion, renderizar_plantilla
from auth.models import PreguntasSecretas, UserProfile
from personas.models import Personas
from umail import settings

@csrf_protect
def contactos(request, template_name='usuario/contactos/contactos.html', mensaje=''):
    c = {}
    c.update(csrf(request))
    c.update({'request':request})
    from django_messages.models import Destinatarios
    from auth.models import Group
    lista_destinatarios = Destinatarios.objects.exclude(grupos__in=Group.objects.all())
    opcion = 'Listado de contactos'
    form = FiltroForm

    if request.method == "POST":
        form = FiltroForm(request.POST)
        if form.is_valid():
            q = request.POST['filtro']
            lista_destinatarios = lista_destinatarios.filter(models.Q(usuarios__user__userprofile__persona__primer_nombre__icontains=q)| # Primer nombre
                                                            models.Q(usuarios__user__userprofile__persona__primer_apellido__icontains=q)| # Primer apellido
                                                            models.Q(usuarios__user__userprofile__persona__segundo_nombre__icontains=q)| # Primer apellido
                                                            models.Q(usuarios__user__userprofile__persona__segundo_apellido__icontains=q)| # Primer apellido
                                                            models.Q(usuarios__user__userprofile__persona__email__icontains=q)| # Correo
                                                            models.Q(usuarios__user__userprofile__persona__telefono__icontains=q)| # Telefono
                                                            models.Q(usuarios__user__userprofile__persona__cargo_principal__cargo__name__icontains=q)| # Cargo
                                                            models.Q(usuarios__user__userprofile__persona__cargo_principal__dependencia__departamento__icontains=q)| # Dependencia
                                                            models.Q(usuarios__user__userprofile__persona__cargo_principal__dependencia__siglas__icontains=q) # Dependencia (siglas)

                                                            ).distinct()

            paginador = Paginator(lista_destinatarios, settings.SUIT_CONFIG['LIST_PER_PAGE'])
            pagina = request.GET.get('page')
            try:
                lista_destinatarios = paginador.page(pagina)
            except PageNotAnInteger:
                # If page is not an integer, deliver first page.
                lista_destinatarios = paginador.page(1)
            except EmptyPage:
                # If page is out of range (e.g. 9999), deliver last page of results.
                lista_destinatarios = paginador.page(paginador.num_pages)
            c.update({'form':form})
            c.update({'opcion':opcion})
            c.update({'lista_destinatarios':lista_destinatarios})
            print(lista_destinatarios.object_list)

            return render_to_response(template_name, c)
    paginador = Paginator(lista_destinatarios, settings.SUIT_CONFIG['LIST_PER_PAGE'])
    pagina = request.GET.get('page')
    try:
        lista_destinatarios = paginador.page(pagina)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        lista_destinatarios = paginador.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        lista_destinatarios = paginador.page(paginador.num_pages)
    c.update({'form':form})
    c.update({'opcion':opcion})
    c.update({'lista_destinatarios':lista_destinatarios})

    return render_to_response(template_name, c)
contactos = login_required(contactos)

class Perfil(View):
    template = 'usuario/perfil/perfil.html'
    form = PerfilForm
    mensaje = 'Actualiza toda tu información personal para tener siempre tus datos al día'
    (tipo_mensaje, expresion) = msj_expresion('info')

    def get(self, request, *args, **kwargs):
        user_profile = UserProfile.objects.get(user=request.user)
        form = self.form(instance=user_profile.persona, initial={'notificaciones':user_profile.notificaciones, 'num_identificacion':user_profile.persona.num_identificacion})

        return renderizar_plantilla(request, 
                            plantilla = self.template, 
                            tipo_mensaje = self.tipo_mensaje, 
                            expresion = self.expresion, 
                            mensaje = self.mensaje, 
                            form = form,
                        )

    def post(self, request, *args, **kwargs):
        form = self.form(request.POST)
        if form.is_valid():
            primer_nombre = form.cleaned_data['primer_nombre']
            segundo_nombre = form.cleaned_data['segundo_nombre']
            primer_apellido = form.cleaned_data['primer_apellido']
            segundo_apellido = form.cleaned_data['segundo_apellido']
            genero = form.cleaned_data['genero']
            telefono = form.cleaned_data['telefono']
            notificaciones = form.cleaned_data['notificaciones']

            # Buscar persona y usuario
            persona = Personas.objects.get(num_identificacion=request.user.profile.persona.num_identificacion)
            user_profile = UserProfile.objects.get(persona=persona)

            # Buscar asignar datos 
            persona.primer_nombre = primer_nombre
            persona.segundo_nombre = segundo_nombre
            persona.primer_apellido = primer_apellido
            persona.segundo_apellido = segundo_apellido
            persona.genero = genero
            persona.telefono = telefono
            user_profile.notificaciones = notificaciones

            # Guardar registros
            persona.save()
            user_profile.save()

            self.mensaje = '¡Tus datos han sido actualizados exitosamente!'
            self.tipo_mensaje = 'success'

        else:
            self.tipo_mensaje = 'error'
            for error in form.errors:
                self.mensaje = form.errors['%s' %(error)].as_text().replace('* ','') + ": " + error
        (self.tipo_mensaje, self.expresion) = msj_expresion(self.tipo_mensaje)
        return renderizar_plantilla(request, 
                            plantilla = self.template, 
                            tipo_mensaje = self.tipo_mensaje, 
                            expresion = self.expresion, 
                            mensaje = self.mensaje, 
                            form = form,
                        )

@csrf_protect
def password_change(request,
                    template_name='usuario/perfil/cambiar_clave.html',
                    current_app=None, extra_context=None, expresion=None, tipo_mensaje=None, mensaje=None, palabra_clave=None):
    context = {}
    context.update(csrf(request))

    # Determinar cuál formulario usar.
    # 'Asignar' no necesita contraseña anterior
    # 'Cambiar' necesita contraseña anterior
    accion = ''
    if palabra_clave == 'asignar':
        form = SetPasswordForm(user=request.user, data=request.POST or None)
        accion = 'cambiada'
    elif palabra_clave == 'cambiar':
        accion = 'actualizada'
        form = PasswordChangeForm(user=request.user, data=request.POST or None)

    if form.is_valid():
        form.save()
        mensaje = 'Contraseña %s exitosamente' %(accion)
        tipo_mensaje = 'success'
    else:
        tipo_mensaje = 'error'
        for error in form.errors:
            mensaje = form.errors['%s' %(error)].as_text().replace('* ','')

    (tipo_mensaje, expresion) = msj_expresion(tipo_mensaje)
    context.update({'formulario':form})
    context.update({'request':request})
    context.update({'mensaje':mensaje})
    context.update({'tipo_mensaje':tipo_mensaje})
    context.update({'expresion':expresion})
    return render_to_response(template_name, context)
password_change = login_required(password_change)

class Preguntas_Secretas(View):
    tipo_mensaje = ''
    expresion = ''
    mensaje = ''
    template = 'usuario/perfil/preguntas_secretas.html'
    form = PreguntasForm

    def get(self, request, *args, **kwargs):
        try:
            usuario = User.objects.get(id=kwargs['user_id'])
        except:
            raise Http404
        else:
            if usuario.preguntassecretas_set.get_query_set().exists():
                preguntas = PreguntasSecretas.objects.filter(usuario__id=int(kwargs['user_id']))
                preguntas = random.sample(preguntas, 3)
                pregs = []
                for pregunta in preguntas:
                    pregs.append(pregunta.id)
                preguntas = PreguntasSecretas.objects.filter(id__in=pregs)
                form = self.form()

                self.mensaje = 'Para su mayor seguridad debe proporcionar algunas preguntas y respuestas secretas'
                (self.tipo_mensaje, self.expresion) = msj_expresion('alert')
                return renderizar_plantilla(request, 
                                    plantilla = self.template, 
                                    tipo_mensaje = self.tipo_mensaje, 
                                    expresion = self.expresion, 
                                    mensaje = self.mensaje, 
                                    form = form,
                                    extra=preguntas
                                )

            else:
                return HttpResponseRedirect('preguntas_secretas/')

    def post(self, request, *args, **kwargs):
        form = self.form(request.POST)
        if not form.is_valid():
            self.tipo_mensaje = 'error'
            for error in form.errors:
                mensaje = form.errors['%s' %(error)].as_text().replace('* ','')

        pregunta_1 = request.POST['pregunta_1']
        respuesta_1 = request.POST['respuesta_1']
        pregunta_2 = request.POST['pregunta_2']
        respuesta_2 = request.POST['respuesta_2']
        pregunta_3 = request.POST['pregunta_3']
        respuesta_3 = request.POST['respuesta_3']

        # Revisión de respuestas para la pregunta
        pregunta_1 = PreguntasSecretas.objects.get(id__iexact=pregunta_1)
        pregunta_2 = PreguntasSecretas.objects.get(id__iexact=pregunta_2)
        pregunta_3 = PreguntasSecretas.objects.get(id__iexact=pregunta_3)

        if not pregunta_1.respuesta == respuesta_1:
            self.mensaje = '%s no es la respuesta para %s. Por favor inténtelo de nuevo' %(respuesta_1, pregunta_1)
            self.tipo_mensaje = 'error'
        elif not pregunta_2.respuesta == respuesta_2:
            self.mensaje = '%s no es la respuesta para %s. Por favor inténtelo de nuevo' %(respuesta_2, pregunta_2)
            self.tipo_mensaje = 'error'
        elif not pregunta_3.respuesta == respuesta_3:
            self.mensaje = '%s no es la respuesta para %s. Por favor inténtelo de nuevo' %(respuesta_3, pregunta_3)
            self.tipo_mensaje = 'error'

        pregs = []
        if self.tipo_mensaje == 'error':
            pregs.append(pregunta_1.id)
            pregs.append(pregunta_2.id)
            pregs.append(pregunta_3.id)
            preguntas = PreguntasSecretas.objects.filter(id__in=pregs)
            (self.tipo_mensaje, self.expresion) = msj_expresion(self.tipo_mensaje)
            return renderizar_plantilla(request, 
                                plantilla=self.template, 
                                tipo_mensaje = self.tipo_mensaje, 
                                expresion = self.expresion, 
                                mensaje = self.mensaje, 
                                form = form,
                                extra = preguntas,
                            )
        else:
            try:
                usuario = User.objects.get(id=kwargs['user_id'])
            except:
                raise Http404
            else:
                usuario = User.objects.get(id=kwargs['user_id'])
            usuario.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, usuario)
            return HttpResponseRedirect('/perfil/asignar_clave/')
