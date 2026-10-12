from django.urls import re_path as url
#from django.views.generic.simple import redirect_to -> Django 1.4
from django.views.generic import TemplateView # Django 1.5

from django_messages.views import *

urlpatterns = [
    #url(r'^$', redirect_to, {'url': 'inbox/'}, name='messages_redirect'), # Django 1.4
    url(r'^$', TemplateView.as_view(template_name='django_messages/inbox.html'), name='messages_redirect'), # Django 1.5
    url(r'^inbox/$', bandeja, name='messages_inbox'),
    url(r'^outbox/$', outbox, name='messages_outbox'),
    url(r'^compose/$', compose, name='messages_compose'),
    url(r'^compose/(?P<recipient>[\w.@+-]+)/$', compose, name='messages_compose_to'),
    url(r'^reply/(?P<message_id>[\d]+)/$', reply, name='messages_reply'),
    url(r'^view/(?P<message_id>[\d]+)/$', view, name='messages_detail'),
    url(r'^delete/(?P<message_id>[\d]+)/$', delete, name='messages_delete'),
    url(r'^undelete/(?P<message_id>[\d]+)/$', undelete, name='messages_undelete'),
    url(r'^trash/$', trash, name='messages_trash'),
]
