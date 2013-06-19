#-*- coding: utf8  
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext, loader
from django.contrib.auth.decorators import login_required
from django.db import transaction, models
from django.core import serializers
from django.core.context_processors import csrf
from lib import fecha
import datetime
from umail import settings
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT 
from reportlab.pdfgen import  canvas
from reportlab.platypus import SimpleDocTemplate, BaseDocTemplate, Image, Spacer, Paragraph, Table, TableStyle 
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from django.utils import formats
from django.utils.translation import ugettext as _
from reportlab.graphics.barcode import createBarcodeDrawing
from django.utils.text import normalize_newlines
from django.utils.safestring import mark_safe
from reportes.forms import LibroMemoForm

def index(request, template_name='user/reportes/reportes.html'):
    c = {}
    c.update(csrf(request))
    c.update({'request':request})
    c.update(csrf(request))
  
    libro_memo = LibroMemoForm(request.POST)
    if request.method == 'POST':
        if libro_memo.is_valid():
            # Para editar los datos se le pasa el modelform  y se instancia con el request.profile.persona para guardar los cambios realizados
            libro_memo = LibroMemoForm(request.POST, instance=request.user.profile.persona)
            libro_memo.save()

    c.update({'libro_memo':libro_memo})
    return render_to_response(template_name, c)
index = login_required(index)

PAGE_HEIGHT=29.7*cm
PAGE_WIDTH=21*cm

def memo(request, message_id):
    ''' Función para descarga de memorándums en PDF '''
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = u'attachment; filename=Memorándum.pdf; pagesize=A4'

    elementos = []
    doc = SimpleDocTemplate(response)    
    style = getSampleStyleSheet() 
    style2 = getSampleStyleSheet()
    styleFecha = getSampleStyleSheet()
    styleEncabezado = getSampleStyleSheet()

    fechas = datetime.datetime.today()
    mes = fecha.NormalDate().monthName()
    dia = fecha.NormalDate().dayOfWeekName()
    salto = '<br />'

    txtFecha = '%s, %s DE %s DE %s'%(dia.upper(), fechas.day, mes.upper(), fechas.year)
    styleF = styleFecha['Normal']
    styleF.fontSize = 8
    styleF.fontName = 'Helvetica'
    styleF.alignment = TA_RIGHT
    fechaV = Paragraph(txtFecha, styleF)
    elementos.append(fechaV)
    elementos.append(Spacer(1,5))

    #-- Espacio para poner el encabezado con la clase Canvas
    elementos.append(Spacer(1,75))

    from django_messages.models import Message
    memo = Message.objects.get(id=message_id)

    txtTitulo = u'MEMORÁNDUM%s' %(salto)
    if memo.tipo == 'Circular':
        txtTitulo = 'MEMORÁNDUM CIRCULAR'
    titulo = style['Heading1']
    titulo.fontSize = 12
    titulo.fontName = 'Helvetica-Bold'
    titulo.alignment = TA_CENTER
    tituloV = Paragraph(txtTitulo, titulo)
    elementos.append(tituloV)
    elementos.append(Spacer(1,5))

    x = [
    ('BOX', (0,0), (-1,-1), 0.50, colors.black),
    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
    #('TOPPADDING', (0,0), (-1,-1), 1),
    #('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ('GRID', (0,0), (-1,-1), 0.50, colors.black),
    #('FONT', (0,0), (-1,-1), "Helvetica", 8),
    ('FONT', (0,0), (-1,-1), "Helvetica", 6),
    ]

    identificador = '%s.%s.%s - %d %s' %(memo.sender.usuarios.persona.cargo_principal.dependencia.dependencia.nivel, memo.sender.usuarios.persona.cargo_principal.dependencia.nivel, memo.sender.usuarios.persona.cargo_principal.dependencia.siglas, memo.id, salto)

    para = '' 
    for destin in  memo.recipient.get_query_set()[0:memo.recipient.get_query_set().count()-1]:
        para = u'%s, %s' %(destin, para)
    para = u'%s %s' %(para, memo.recipient.get_query_set()[memo.recipient.get_query_set().count()-1])

    para = u'<b>Para: </b> %s %s' %(para, salto)

    de = u'<b>De: </b> %s %s' %(memo.sender, salto)

    memo_mes = fecha.NormalDate(memo.sent_at).monthName()
    memo_dia = fecha.NormalDate(memo.sent_at).dayOfWeekName()
    enviado = '<b>Fecha:</b> %s, %s de %s de %s a las %s:%s:%s'%(memo_dia, memo.sent_at.day, memo_mes, memo.sent_at.year, memo.sent_at.time().hour, memo.sent_at.time().minute, memo.sent_at.time().second)
    enviado = u'<b>Fecha:</b> %s %s' %(enviado, salto)

    txtInfo = '%s %s %s %s' %(identificador, para, de, enviado)
    # Estilo txtInfo
    info = style['Normal']
    info.fontSize = 12
    info.alignment = TA_LEFT
    info.fontName = 'Helvetica'
    infoV = Paragraph(txtInfo, info)
    elementos.append(infoV)
    elementos.append(Spacer(1,10))

    autoescape = None
    autoescape = autoescape and not isinstance(memo.body, SafeData)
    memo.body = normalize_newlines(memo.body)

    texto = salto + mark_safe(memo.body.replace('\n', '<br />'))

    #---> Estilo de la variable texto
    parrafo = style2['Normal']
    parrafo.fontsize = 12
    parrafo.fontName = 'Helvetica'
    parrafo.alignment = TA_JUSTIFY
    parrafo.spaceBefore = 5
    parrafo.firstLineIndent = 20

    Parrafo1 = Paragraph(u'%s'%(texto), parrafo)
    elementos.append(Parrafo1)
    elementos.append(Spacer(3,30))

    # Inicio código de barras
    codigoBarra_style = getSampleStyleSheet()
    codigoBarra = codigoBarra_style['Normal']
    codigoBarra.fontSize = 12
    codigoBarra.fontName = 'Courier'
    codigoBarra.alignment = TA_RIGHT

    st = createBarcodeDrawing('Code128',value = str(memo.codigo), barWidth= 0.040*cm, barHeight=0.500*cm, lquiet=11.500*cm)
    elementos.append(st)
    txtCodigoBarra = Paragraph(str(memo.codigo), codigoBarra)
    elementos.append(txtCodigoBarra)
    # Fin código de barras

    #doc.build(elementos, canvasmaker=NumeroDePagina, onFirstPage=encabezado_constancia)
    doc.build(elementos, canvasmaker=pieDePaginaConstancias, onFirstPage=encabezado_constancia)
    return response  
memo = login_required(memo)

def encabezado_constancia(canvas, doc):
    canvas.saveState()
    canvas.drawImage(settings.STATIC_ROOT+'images/unerg.jpg', 2.6*cm, PAGE_HEIGHT-4.5*cm, width = 100, height = 38)
    canvas.setFont("Helvetica-Bold",10)
    canvas.drawCentredString(PAGE_WIDTH-9.5*cm, PAGE_HEIGHT-3.6*cm, u'REPÚBLICA BOLIVARIANA DE VENEZUELA')
    canvas.drawCentredString(PAGE_WIDTH-9.5*cm, PAGE_HEIGHT-4.0*cm, u'UNIVERSIDAD NACIONAL EXPERIMENTAL RÓMULO GALLEGOS')
    canvas.drawCentredString(PAGE_WIDTH-9.5*cm, PAGE_HEIGHT-4.4*cm, u'DIRECCIÓN DE ADMISIÓN, CONTROL Y EVALUACIÓN')
    canvas.restoreState()
    canvas.saveState()

class NumeroDePagina(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """add page info to each page (page x of y)"""
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        fechas = datetime.datetime.today()
        self.setFont("Helvetica-Bold", 6)
        self.drawRightString(129*mm, 6*mm,
            u"%02d/%02d/%d   %02d:%02d:%02d    Página %d de %d" % (fechas.day,fechas.month,fechas.year, fechas.hour, fechas.minute, fechas.second, self._pageNumber, page_count))

class pieDePaginaConstancias(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """add page info to each page (page x of y)"""
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)
    def draw_page_number(self, page_count):
        fechas = datetime.datetime.today()
        self.setFont("Helvetica-Bold", 6)
        self.drawRightString(129*mm, 6*mm,
            u"%02d/%02d/%d   %02d:%02d:%02d    Página %d de %d" % (fechas.day,fechas.month,fechas.year, fechas.hour, fechas.minute, fechas.second, self._pageNumber, page_count))