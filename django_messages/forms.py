# -*- coding: utf8 -*-
import datetime
from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _ 
from django_select2.forms import ModelSelect2MultipleWidget
from django.contrib.auth.models import User
from django_messages.models import *
from django_summernote.widgets import SummernoteWidget

if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification
else:
    notification = None

from django_messages.models import Message
from django_messages.fields import CommaSeparatedUserField

class BandejaForm(forms.Form):
    mensajes = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple)
    class Meta:
        widgets = {
              'mensaje': SummernoteWidget(),
              }

class DestinatariosWidget(ModelSelect2MultipleWidget):
    model = Destinatarios
    search_fields = [
        'usuarios__persona__primer_nombre__icontains',
        'usuarios__persona__primer_apellido__icontains',
        'usuarios__persona__segundo_nombre__icontains',
        'usuarios__persona__segundo_apellido__icontains',
        'usuarios__persona__email__icontains',
        'grupos__name__icontains',
    ]


class ComposeForm(forms.ModelForm):
    recipient = forms.ModelMultipleChoiceField(
        queryset=Destinatarios.objects.all(), required=False, label='Destinatario',
        widget=DestinatariosWidget(attrs={'data-placeholder': 'Usuario o grupo'}))
    con_copia = forms.ModelMultipleChoiceField(
        queryset=Destinatarios.objects.all(), required=False,
        widget=DestinatariosWidget(attrs={'data-placeholder': 'Usuario o grupo'}))

    body = forms.CharField(widget=SummernoteWidget())

    class Meta:
        model = Message
        exclude = ('recipient', 'con_copia', 'body')
        fields = ('archivo', 'subject')
        widgets = {
                  'subject': forms.TextInput(attrs={'placeholder':'Resumen del memorándum', 'class':'input-xxlarge'}),
                  }
    def clean(self):
        # Si hizo click en enviar, debe validar todos los campos
        if 'enviar' in self.data:
            # Validar destinatario obligatorio
            if 'recipient' not in self.data:
                raise forms.ValidationError('No seleccionó ningún destinatario. Por favor, indique para quién es el memorándum')

            # Validar asunto obligatorio
            if self.cleaned_data['subject'] == '':
                raise forms.ValidationError('No introdujo ningún asunto. Por favor ingrese el resumen del contenido del memorándum')

            # Validar cuerpo obligatorio
            if 'body' not in self.data:
                raise forms.ValidationError('No introdujo ningún mensaje. Por favor ingrese el contenido del memorándum')

        for con_copia in self.cleaned_data['con_copia']:
            if self.cleaned_data['recipient'].__contains__(con_copia):
                raise forms.ValidationError('%s está "con copia" y se encuentra entre los destinatarios. Debe estar sólo en uno de ambos campos' %(con_copia))

        return self.cleaned_data


