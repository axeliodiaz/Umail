# -*- coding: utf8 -*-
import datetime
from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _ 
from django_select2 import *
from suit_redactor.widgets import RedactorWidget
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

class ComposeForm(forms.ModelForm):
    recipient = ModelSelect2MultipleField(
                                        queryset=Destinatarios.objects, 
                                        required=False, 
                                        label='Destinatario', 
                                        search_fields = ('usuarios__persona__primer_nombre__icontains', #primer nombre
                                                        'usuarios__persona__primer_apellido__icontains', #primer apellido
                                                        'usuarios__persona__segundo_nombre__icontains', #segundo nombre
                                                        'usuarios__persona__segundo_apellido__icontains', #segundo apellido
                                                        'usuarios__email__icontains') #email
                                            )
    recipient.widget.set_placeholder('Usuario o grupo') # Asignar un placeholder al campo

    con_copia = ModelSelect2MultipleField(queryset=Destinatarios.objects, 
                                        required=False,
                                        search_fields = ('usuarios__persona__primer_nombre__icontains', #primer nombre
                                                        'usuarios__persona__primer_apellido__icontains', #primer apellido
                                                        'usuarios__persona__segundo_nombre__icontains', #segundo nombre
                                                        'usuarios__persona__segundo_apellido__icontains', #segundo apellido
                                                        'usuarios__email__icontains') #email
                                        )
    con_copia.widget.set_placeholder('Usuario o grupo') # Asignar un placeholder al campo

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


