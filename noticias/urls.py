from noticias import views
# -*- coding: utf-8 -*-
from django.urls import re_path as url
urlpatterns=[
    url(r'^(\d+)$',views.detalle_noticia, name='detalle_noticia'),
    url(r'^.*$', views.todas_noticias), #Vista por defecto
]
