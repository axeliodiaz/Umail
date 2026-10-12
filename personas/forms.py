# -*- coding: utf8 -*-
from django import forms
from personas.models import Personas
from auth.models import PreguntasSecretas, UserProfile
import random

class PerfilForm(forms.ModelForm):
    notificaciones = forms.BooleanField(required=False,help_text='Active si desea enviar notificaciones a su correo electrónico')
    num_identificacion = forms.CharField(required=False)
    class Meta:
        model = Personas
        exclude = ('tipodoc','num_identificacion','cargo_principal','cargos_autorizados')
    def __init__(self, *args, **kwargs):
        super(PerfilForm, self).__init__(*args, **kwargs)
        self.fields['email'].widget.attrs['readonly'] = True
        self.fields['num_identificacion'].widget.attrs['readonly'] = True


class FiltroForm(forms.Form):
    filtro = forms.CharField()

class PreguntasForm(forms.Form):
    respuesta_1 = forms.CharField(widget=forms.TextInput(attrs={'required':'required'}))
    respuesta_2 = forms.CharField(widget=forms.TextInput(attrs={'required':'required'}))
    respuesta_3 = forms.CharField(widget=forms.TextInput(attrs={'required':'required'}))
