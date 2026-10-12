# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from auth.models import *

class AuthenticacionForm(AuthenticationForm):
    username = forms.CharField(label="Correo", max_length=200, widget = forms.TextInput(attrs={'type':'text', 'class':'input-block-level', 'required':'required'}))
    password = forms.CharField(max_length=200, widget = forms.PasswordInput(attrs={'type':'password', 'class':'input-block-level','required':'required'}))

    def __init__(self, request=None, *args, **kwargs):       
        super(AuthenticacionForm, self).__init__(*args, **kwargs)
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        if username and password:
            self.user_cache = authenticate(username=username, password=password)
            if self.user_cache is None:
                raise forms.ValidationError("Introduzca el usuario y/o contraseña correcta.")
            elif not self.user_cache.is_active:
                raise forms.ValidationError("Esta cuenta está inactiva.")

class PreguntasForm(forms.ModelForm):
    class Meta:
        model = PreguntasSecretas
        exclude = ('usuario',)

        widgets = {
              'pregunta': forms.Select(attrs={'required':'required'}),
              'respuesta': forms.TextInput(attrs={'required':'required'})
              }
