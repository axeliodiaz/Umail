# -*- coding: utf8 -*-
from django import forms
from django_messages.models import Message
from umail import settings
from django.contrib.admin import widgets
from django.utils.safestring import mark_safe
from reportes.models import Comentarios, Respuestas
from suit_redactor.widgets import RedactorWidget


class HorizontalRadioRenderer(forms.RadioSelect.renderer):
    def render(self):
        return mark_safe('\n'.join(['%s\n' % w for w in self]))

OPCIONES = [('entrada', 'Entrada',), ('salida', 'Salida',), ('ambos','Ambos')]
class LibroMemoForm(forms.Form):
    opcion = forms.ChoiceField(choices=OPCIONES, widget=forms.RadioSelect(renderer=HorizontalRadioRenderer))
    fecha_inicio = forms.CharField()
    fecha_fin = forms.CharField()
    class Meta:

        widgets = {
            'fecha_inicio': forms.TextInput(attrs={'type':'text', 'class':'input', 'required':'required', 'value':'','name':'fecha_inicio','id':'datepicker1','placeholder':'fecha inicial'}),
            'fecha_fin': forms.TextInput(attrs={'type':'text', 'class':'input', 'required':'required', 'value':'','name':'fecha_fin','id':'datepicker2','placeholder':'fecha final'}),
            }

    def __init__(self, *args, **kwargs):
        super(LibroMemoForm, self).__init__(*args, **kwargs)
        self.fields['fecha_inicio'].widget = self.Meta.widgets['fecha_inicio']
        self.fields['fecha_fin'].widget = self.Meta.widgets['fecha_fin']

class ConsultaMemoForm(forms.Form):
    codigo = forms.IntegerField(required=False)

class RespuestaForm(forms.ModelForm):
    class Meta:
        model = Respuestas
        widgets = {
                  'comentario': RedactorWidget(editor_options={'lang': 'es'})
                  }
    ordering = ('-respondido',)

class ComentariosForm(forms.ModelForm):
    class Meta:
        model = Comentarios
        widgets = {
                  'comentario': RedactorWidget(editor_options={'lang': 'es'})
                  }
    ordering = ('-respondido',)

