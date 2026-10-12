# -*- coding: utf-8 -*-
from noticias.models import *
from django.core.context_processors import csrf
from django.shortcuts import render_to_response, render
from auth.forms import AuthenticacionForm, PreguntasForm
from django.contrib.auth import authenticate
from django.contrib.auth.views import login
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from reportes.models import Comentarios, Respuestas
from lib.umail import msj_expresion, renderizar_plantilla
from django.template import RequestContext
from django.views.generic.base import View
from django.forms.formsets import formset_factory
from django.forms.models import modelformset_factory
from auth.models import PreguntasSecretas, Pregunta
from datetime import datetime, timedelta 
from umail import settings 
from django.contrib import auth 

class Ayuda(View):
    secciones = [
                'email', 
                'perfil', 
                'contactos',
                'admin',
                'reportes',
                'archivos',
                'seguridad',
                ]
    def get(self, request, *args, **kwargs):
        seccion = kwargs['seccion'].lower()
        if not seccion.lower() in self.secciones:
            return HttpResponseRedirect('/ayuda')
        else:
            template = 'usuario/manual/seccion_%s.html' %(seccion)
            return renderizar_plantilla(request, 
                                plantilla = template, 
                            )

class AutoLogout: 
    def process_request(self, request): 
        if not request.user.is_authenticated() : 
            return 

        try: 
            if datetime.now() - request.session['last_touch'] > timedelta( 0, settings.AUTO_LOGOUT_DELAY * 60, 0): 
                auth.logout(request) 
                del request.session['last_touch'] 
                return 
        except KeyError: 
            pass 

        request.session['last_touch'] = datetime.now()

class Auth(View):
    tipo_mensaje = ''
    expresion = ''
    mensaje = ''
    form = AuthenticacionForm
    noticias = Noticias.objects.all().order_by('-fecha')[:3] # Últimas 3 noticias
    template = 'usuario/auth/login.html'
    diccionario = {}
    diccionario.update({'noticias':noticias})
    
    def get(self, request, *args, **kwargs):
        self.form = self.form()
        if request.user.is_authenticated():
            if request.GET.has_keys['next']:
                return HttpResponseRedirect(request.GET['next'])
            else:
                return HttpResponseRedirect('/')
            
        return renderizar_plantilla(request, 
                            plantilla = self.template, 
                            tipo_mensaje = self.tipo_mensaje, 
                            expresion = self.expresion, 
                            mensaje = self.mensaje, 
                            form = self.form
                        )

    def post(self, request, *args, **kwargs):
        form = self.form(request.POST)
        self.diccionario.update({'form':self.form})
        usuario = User.objects.filter(Q(username=request.POST['username'])|Q(email=request.POST['username']))
        self.diccionario.update({'request':request})
        if usuario.exists(): 
            usuario = usuario[0]
            user = authenticate(username=usuario, password=request.POST['password'])

            if user is not None:
                login(request, usuario)
                #"User is not valid, active and authenticated"
                if not user.is_active:
                    self.mensaje = "La contraseña es válida pero la cuenta ha sido desactivada"
                    (self.tipo_mensaje, self.expresion) = msj_expresion('error')
                    return renderizar_plantilla(request, 
                                        plantilla = self.template, 
                                        tipo_mensaje = self.tipo_mensaje, 
                                        expresion = self.expresion, 
                                        mensaje = self.mensaje, 
                                        form = form
                                    )
                else:
                    # El usuario se loggea correctamente
                    return HttpResponseRedirect('/preguntas_secretas/')
            else:
                # El usuario o contraseña eran incorrectos
                self.mensaje = "Contraseña incorrecta. Por favor, inténtelo nuevamente"
                (self.tipo_mensaje, self.expresion) = msj_expresion('error')
                return renderizar_plantilla(request, 
                                    plantilla = self.template, 
                                    tipo_mensaje = self.tipo_mensaje, 
                                    expresion = self.expresion, 
                                    mensaje = self.mensaje, 
                                    form = form
                                )
        else:
            # El usuario no existe
            self.mensaje = "No existe el usuario %s. Por favor, confirme sus datos" %(request.POST['username'])
            (self.tipo_mensaje, self.expresion) = msj_expresion('error')
            form = self.form(request.POST)
            return renderizar_plantilla(request, 
                                plantilla = self.template, 
                                tipo_mensaje = self.tipo_mensaje, 
                                expresion = self.expresion, 
                                mensaje = self.mensaje, 
                                form = form
                            )

from django.db import transaction

class Revisar_preguntas(View):
    from django.forms.formsets import formset_factory
    tipo_mensaje = ''
    expresion = ''
    mensaje = ''
    template = 'usuario/auth/preguntas.html'
    form = formset_factory(PreguntasForm, extra = 6)

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            if not request.user.preguntassecretas_set.get_query_set().exists():
                form = self.form()
                self.mensaje = 'Para su mayor seguridad debe proporcionar algunas preguntas y respuestas secretas'
                (self.tipo_mensaje, self.expresion) = msj_expresion('alert')
                return renderizar_plantilla(request, 
                                    plantilla = self.template, 
                                    tipo_mensaje = self.tipo_mensaje, 
                                    expresion = self.expresion, 
                                    mensaje = self.mensaje, 
                                    form = form 
                                )

            else:
                return HttpResponseRedirect('/')
        else:
            return HttpResponseRedirect('/auth')

    @transaction.commit_on_success
    def post(self, request, *args, **kwargs):
        
        form = self.form(request.POST)
        error = False

        if form.is_valid():
            posicion = 0
            usuario = request.user
            transaction.savepoint()

            for formulario in form.forms:
                pregunta = formulario['pregunta'].data
                pregunta = Pregunta.objects.get(id=pregunta)
                respuesta = formulario['respuesta'].data
                pregunta_secreta = PreguntasSecretas.objects.filter(usuario=usuario, pregunta=pregunta)
                if not pregunta_secreta.exists():
                    PreguntasSecretas.objects.create(usuario=usuario, pregunta=pregunta, respuesta=respuesta)
                else:
                    (self.tipo_mensaje, self.expresion) = msj_expresion('error')
                    self.mensaje = 'Al parecer la pregunta "%s" ya la has elegido más de una vez.' %(pregunta)
                    error=True

            if not error:
                transaction.commit()
                return HttpResponseRedirect('/')
            else:
                transaction.rollback()
                return renderizar_plantilla(request, 
                                    plantilla=self.template, 
                                    tipo_mensaje = self.tipo_mensaje, 
                                    expresion = self.expresion, 
                                    mensaje = self.mensaje, 
                                    form = form
                                )

def index(request):
    import datetime
    fecha_actual = datetime.datetime.today()
    diccionario = {}
    diccionario.update(csrf(request))
    diccionario.update({'request':request})
    diccionario.update({'fecha':fecha_actual})
    ultimas_noticias1 = Noticias.objects.all().order_by('-fecha')[:3]
    diccionario.update({'ult_notic1':ultimas_noticias1})
    mensaje = '' 
    loggeado = False

    return render_to_response('usuario/auth/index.html', diccionario)

def revisar_comentario(request):
    from umail.settings import ADMINS
    from django.contrib.sites.models import Site
    from lib.umail import enviar_email

    correos = []
    for admin in ADMINS:
        correos.append(admin[1])

    if request.method == 'POST':
        pregunta = request.POST['pregunta']
        comentario = request.POST['comentario']
        nombre = request.POST['nombre']
        correo = request.POST['correo']
        archivo = request.POST['archivo']
        comentario = Comentarios.objects.create(
                                                pregunta = pregunta,
                                                comentario = comentario,
                                                nombre = nombre,
                                                correo = correo,
                                                archivo = archivo 
                                                )

        # Enviar correo a los administradores del sistema
        asunto = "Pregunta nueva"
        contenido = 'Tiene un comentario de %s preguntando "%s" con el siguiente mensaje: %s. \n\nTambién puede visitar el mensaje en %s/admin/reportes/comentarios/%s' %(comentario.correo, comentario.pregunta, comentario.comentario, Site.objects.get_current(), comentario.id)
        enviar_email(asunto=asunto, contenido=contenido, correos=correos)

        # Se crea una respuesta tentativa
        respuesta = Respuestas.objects.create(
                                               pregunta = comentario,
                                               comentario = '',
                                               usuario = None,
                                               respondido = False,
                                              )
        return HttpResponseRedirect(request.POST['url'])

