from django.utils.safestring import mark_safe
# -*- coding: utf8 -*-
from django import template
from django.utils.html import escape
from django.utils.html import format_html
from django_messages.models import Message
from auth.models import User

register = template.Library()
def responder_memo(memo,arg):
    memo = Message.objects.get(id=memo)
    user = User.objects.get(id=arg)
    respondercon_copia = False
    con_copia = False
    tabla = ''

    destinatario = memo.recipient

    if destinatario.grupos == None:
        if destinatario.usuarios.user == user and not con_copia:
            tabla = '<a href="/responder/' + str(memo.id) + '">Responder</a> <a href="/descargas/memo/' + str(memo.id) + '"Descargar</a><a href="/archivar/' + str(memo.id) + '" Archivar</a>'
    elif destinatario.usuarios == None:
        if user in destinatario.grupos.user_set.all():
            tabla = '<a href="/responder/' + str(memo.id) + '" Responder</a> <a href="/archivar/' + str(memo.id) + '" Archivar</a>'
    return mark_safe(tabla)
responder_memo.is_safe = True 
register.filter(responder_memo)

