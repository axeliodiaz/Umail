# -*- coding: utf-8 -*-
from django.conf.urls import include
from django.urls import re_path as url
from django.views.static import serve as static_serve
from django.contrib.auth.views import LogoutView
import auth.views as auth_views
import django_messages.views as messages_views
import personas.views as personas_views
import reportes.views as reportes_views

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from auth.views import *
from django.contrib.auth.decorators import login_required
from manual_usuario.views import Manual


urlpatterns = [
    
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^noticias/', include('noticias.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'logout$', LogoutView.as_view(next_page='/'), name='salir'),
    url(r'^$',auth_views.index, name='inicio'),
    url(r'^revisar_comentario$',auth_views.revisar_comentario, name='comentario'),
    url(r'^select2/', include('django_select2.urls')),
    url(r'^summernote/', include('django_summernote.urls')),
    url(r'^media/(?P<path>.*)$', static_serve, {'document_root': settings.MEDIA_ROOT}),

    # Auth
    url(r'^auth$', Auth.as_view(), name='auth'),
    url(r'^preguntas_secretas/$', login_required(Revisar_preguntas.as_view(), login_url='/auth'), name='preguntas_secretas'),

    # Manual de usuario 
    url(r'^ayuda/(?P<manual_id>[\d]+)/$', Manual.as_view(), name='seccion'),
    url(r'^ayuda/$', Manual.as_view(), name='manual'),

    # Memos
    ## Bandejas
    url(r'^bandeja/(?P<tipo_bandeja>\w+)/$', messages_views.bandeja, name='bandeja'),

    ## Entrada
    url(r'^entrada/$', messages_views.bandeja, name='messages_inbox'),

    ## Enviados
    url(r'^enviados/$', messages_views.outbox, name='messages_outbox'),

    ## Memos por aprobar
    url(r'^por_aprobar/$', messages_views.por_aprobar, name='por_aprobar'),
    url(r'^por_aprobar/(?P<message_id>[\d]+)/$', messages_views.ver_por_aprobar, name='ver_por_aprobar'),

    ## Memo para aprobar
    url(r'^aprobar/(?P<message_id>[\d]+)/$', messages_views.aprobar, name='aprobar'),

    ## Memo para anular
    url(r'^anular/(?P<message_id>[\d]+)/$', messages_views.anular, name='anular'),

    ## Redactar memo
    url(r'^redactar/(?P<message_id>[\d]+)/$$', messages_views.compose, name='redactar'),
    url(r'^redactar/$', messages_views.compose, name='redactar'),

    ## Responder memo
    url(r'^responder/(?P<message_id>[\d]+)/$', messages_views.reply, name='responder'),
    ## Archivar memo
    url(r'^archivar/(?P<message_id>[\d]+)/$', messages_views.delete, name='archivados'),

    ## Memos archivados
    url(r'^archivados/$', messages_views.trash, name='messages_trash'),

    ## Leer memo
    url(r'^leer/(?P<message_id>[\d]+)/$', messages_views.view, name='leer'),
    url(r'^previsualizar/(?P<message_id>[\d]+)/$', messages_views.view, name='previsualizar'),


    # Personas
    ## Perfil
    url(r'^perfil/', include('personas.urls')),

    url(r'^contactos/', personas_views.contactos, name='contactos'),

    # Reportes
    ## Perfil
    url(r'^reportes/$', reportes_views.index, name='reportes'),
    url(r'^descargas/memo/(?P<message_id>[\d]+)/$', reportes_views.memo, name='descargar'),
]
