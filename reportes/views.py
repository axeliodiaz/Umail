#-*- coding: utf8  
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext, loader
from django.contrib.auth.decorators import login_required
from umail import settings
from django.db import transaction, models
from django.core import serializers
from reportlab.lib.colors import black
from django.core.context_processors import csrf
from lib import fecha
import datetime
from lib.umail import msj_expresion
from umail import settings
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT 
from reportlab.pdfgen import  canvas
from reportlab.platypus import SimpleDocTemplate, BaseDocTemplate, Image, Spacer, Paragraph, Table, TableStyle 
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, cm, mm
from django.utils import formats
from django.utils.translation import ugettext as _
from reportlab.graphics.barcode import createBarcodeDrawing
from django.utils.text import normalize_newlines
from django.utils.safestring import mark_safe
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from reportes.forms import LibroMemoForm, ConsultaMemoForm
from django_messages.models import Message, Destinatarios

def jefe_dep(request):
    return Destinatarios.objects.get(usuarios__user__userprofile__persona__cargo_principal__dependencia = request.user.profile.persona.cargo_principal.dependencia, usuarios__user__userprofile__persona__cargo_principal__cargo = request.user.profile.persona.cargo_principal.dependencia.cargo_max)

def user_destin(request):
    return Destinatarios.objects.get(usuarios__user = request.user)

def revisar_fechas(fecha_inicio, fecha_fin):
    valido = True
    mensaje = ''
    if fecha_inicio > fecha_fin:
        mensaje = 'La fecha de inicio no puede ser mayor a la fecha final. Por favor corrija este error.'
        valido = False
    return valido, mensaje


def index(request, template_name='usuario/reportes/reportes.html', mensaje=''):
    jefe = jefe_dep(request)
    usuario = user_destin(request)
    dependencia = request.user.profile.persona.cargo_principal.dependencia
    c = {}
    c.update(csrf(request))
    c.update({'request':request})
    c.update(csrf(request))
    fecha_actual = datetime.datetime.today()
    c.update({'fecha_actual':fecha_actual})
    from django.contrib.admin.models import LogEntry
    log_user = LogEntry.objects.filter(
        user_id         = request.user.pk, 
        ).order_by('-action_time')[:4]
  
    libro_memo = LibroMemoForm(request.POST)
    consulta_memo = ConsultaMemoForm(request.POST)
    c.update({'log_user':log_user})
    c.update({'mensaje':mensaje})
    c.update({'libro_memo':libro_memo})
    c.update({'consulta_memo':consulta_memo})
    (tipo_mensaje, expresion) = msj_expresion('error')
    c.update({'tipo_mensaje':tipo_mensaje})
    c.update({'expresion':expresion})
    

    if request.method == 'POST':
        c.update({'consulto':False})
        resultado_memo = []
        if consulta_memo.is_valid():
            if consulta_memo['codigo'].data:

                codigo = request.POST['codigo']
                resultado_memo = Message.objects.filter(codigo=codigo).exclude(status__nombre='Anulado')
                c.update({'memo_result':resultado_memo})
                if resultado_memo.exists():
                    resultado_memo = resultado_memo[0]
                    asunto = resultado_memo.subject
                    hora = resultado_memo.sent_at
                    sender = resultado_memo.sender
                    destinos = resultado_memo.recipient
                    if destinos == None:
                        mensaje = "Ese memorándum no tiene todavía un destinatario."
                        (tipo_mensaje, expresion) = msj_expresion('error')
                    else:
                        memo = resultado_memo
                        # Si el memorándum es para el usuario conectado, o lo redactó él o es el jefe de la dependencia, entonces puede descargar el memorándum.
                        descargable = False
                        if request.user.profile.persona == destinos.usuarios.persona or request.user.profile.persona == sender.usuarios.persona or request.user.profile.persona == jefe.usuarios.persona:
                            descargable = True
                        c.update({'jefe':jefe})
                        c.update({'asunto':asunto})
                        c.update({'hora':hora})
                        c.update({'sender':sender})
                        c.update({'destinos':destinos})
                        c.update({'descargable':descargable})
                        c.update({'memo':memo})
                        
                        if resultado_memo.status.nombre == 'Aprobado':
                            c.update({'aprobado':True})
                        else:
                            c.update({'aprobado':False})

                consulta_memo = ConsultaMemoForm(request.POST)
                c.update({'consulta_memo':consulta_memo})

                # Saber si consultó algún memorándum
                c.update({'consulto':True})
                return render_to_response(template_name, c)

        else:
            mensaje = consulta_memo.errors['codigo']

        if libro_memo.is_valid():
            hora_inicio = datetime.time(0,00)
            hora_fin = datetime.time(23,59)

            # Se convierte el string a fecha + hora
            fecha_inicio = request.POST['fecha_inicio'] + ' '+ str(hora_inicio)
            fecha_inicio = datetime.datetime.strptime(fecha_inicio, '%m/%d/%Y %H:%M:%S')
            fecha_fin = request.POST['fecha_fin'] + ' ' + str(hora_fin)
            fecha_fin = datetime.datetime.strptime(fecha_fin, '%m/%d/%Y %H:%M:%S')
            opcion = request.POST['opcion']

            # La fecha de inicio no puede ser mayor a la final
            (valido, mensaje) = revisar_fechas(fecha_inicio, fecha_fin)
            if valido == False:
                c.update({'mensaje':mensaje})
                c.update({'libro_memo':libro_memo})
                return render_to_response(template_name, c)

            # Opciones de libro
            #   'entrada': Memos para el usuario
            #   'salida': Memos escritos por el usuario. Si es el fefe, entonces enviados de la dependencia
            #   'ambos': Memos para el usuario y memos escritos por el usuario. Si es el jefe entonces enviados de la dependencia
            lista_mensajes = Message.objects.filter(sent_at__range=(fecha_inicio, fecha_fin),)
            if opcion == 'entrada':
                # Si no es el jefe, entonces sólo verá los mensajes que son para él
                if jefe == usuario:
                    lista_mensajes = lista_mensajes.filter(recipient__usuarios__user__userprofile__persona__cargo_principal__dependencia=dependencia)
                else:
                    lista_mensajes = lista_mensajes.filter(recipient__id__exact=usuario.id)


            elif opcion == 'salida':
                if jefe == usuario:
                    lista_mensajes = lista_mensajes.filter(sender__usuarios__user__userprofile__persona__cargo_principal__dependencia=dependencia)
                else:
                    lista_mensajes = lista_mensajes.filter(sender = usuario)

            elif opcion == 'ambos':
                if jefe == usuario:
                    lista_mensajes = lista_mensajes.filter(models.Q(recipient__usuarios__user__userprofile__persona__cargo_principal__dependencia=dependencia)|models.Q(sender__usuarios__user__userprofile__persona__cargo_principal__dependencia=dependencia))
                else:
                    lista_mensajes = lista_mensajes.filter(models.Q(sender = usuario)|models.Q(recipient__id__exact=usuario.id))

            # Si no hay ningún mensaje en ese rango de fechas
            memos = lista_mensajes
            if not lista_mensajes.exists():
                mensaje = 'No existe ningún memorándum entre las fechas seleccionadas.'
                c.update({'mensaje':mensaje})
                c.update({'libro_memo':libro_memo})
            else:
                paginador = Paginator(memos, settings.SUIT_CONFIG['LIST_PER_PAGE'])
                page = request.GET.get('page')
                try:
                    memos = paginador.page(page)
                except PageNotAnInteger:
                    # If page is not an integer, deliver first page.
                    memos = paginador.page(1)
                except EmptyPage:
                    # If page is out of range (e.g. 9999), deliver last page of results.
                    memos = paginador.page(paginator.num_pages)
                c.update({'memos':memos})
                c.update({'opcion':opcion})
                lista_mensajes = ''
                for memo in memos:
                    lista_mensajes = str(memo.id) + ',' + lista_mensajes
                c.update({'lista_mensajes':lista_mensajes}) # pasamos la misma variable de memos pero para traernosla de vuelta en el hidden para sacar el PDF
            return render_to_response(template_name, c)
        else:
            if 'opcion' not in request.POST and 'codigo' not in request.POST:
                mensaje = 'Debe elegir un tipo de libro de memos.'
                c.update({'tipo_mensaje':tipo_mensaje})
                c.update({'mensaje':mensaje})
                c.update({'expresion':expresion})
                c.update({'request':request})
                c.update({'libro_memo':libro_memo})
                c.update({'consulta_memo':consulta_memo})
                return render_to_response(template_name, c)
        if 'lista_mensajes' in request.POST:
            memos = request.POST['lista_mensajes']
            opcion = request.POST['opcion']
            memos = memos.split(',')
            lista_mensaje = []
            if opcion == 'salida':
                opcion = 'enviados'
            elif opcion == 'entrada':
                opcion = 'recibidos'
            for memo in memos:
                if memo:
                    lista_mensaje.append(memo)
            memos = Message.objects.filter(id__in=lista_mensaje)
            fecha_inicio = request.POST['fecha_inicio']
            fecha_fin = request.POST['fecha_fin']
            salto = '<br />'

            #Libro_Memos_PDF(request, lista_mensajes)
            #def Libro_Memos_PDF(request, memos):
            response = HttpResponse(mimetype='application/pdf')
            if opcion == 'ambos':
                response['Content-Disposition'] = 'attachment; filename=Libro_memorandum_enviados_recibidos.pdf; pagesize=A4;'
                opcion = 'enviados y recibidos'
            else:
                response['Content-Disposition'] = 'attachment; filename=Libro_memorandum_'+ opcion +'.pdf; pagesize=A4;'

            #elementos es la lista donde almaceno todos lo que voy a incluir al documento pdf
            elementos = []

            # SimpleDocTemplate es la clase para generar el pdf
            doc = SimpleDocTemplate(response)

            style = getSampleStyleSheet()
            styleFecha = getSampleStyleSheet()

            fechas = datetime.datetime.today()
            mes = fecha.NormalDate().monthName() # esta variable contiene el nombre del mes actual a partir de la libreria fecha añadida en lib/
            dia = fecha.NormalDate().dayOfWeekName() # esta variable contiene el dia actual a partir de la libreria fecha añadida en lib/

            #Espacio para poner el encabezado con la clase Canvas
            elementos.append(Spacer(1,40))


            # Estilos de la tabla.
            x = [
            #('BOX', (0,0), (4,0), 0.60, colors.black),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('TOPPADDING', (0,0), (-1,-1), 1),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('GRID', (0,0), (-1,-1), 0.80, colors.black),
            ('FONT', (0,0), (-1,-1), "Helvetica", 7),
            ('FONT', (0,0), (5,0), "Helvetica-Bold", 7),
            ('ALIGN', (1,1), (2,-1), 'CENTER'),
            ]

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

            txtFecha = '%s, %s %s %s'%(dia.upper(), fechas.day, mes.upper(), fechas.year)
            styleF = styleFecha['Normal']
            styleF.fontSize = 8
            styleF.fontName = 'Helvetica'
            styleF.alignment = TA_RIGHT
            fechaV = Paragraph(txtFecha, styleF)
            elementos.append(fechaV)
            elementos.append(Spacer(1,5))

            #-- Espacio para poner el encabezado con la clase Canvas
            elementos.append(Spacer(1,75))

            #Titulo del reporte
            txtTitulo = 'LIBRO DE MEMORÁNDUM %s%s' %(opcion.upper(), str(salto)*2)
            titulo = style['Heading1']
            titulo.fontSize = 9
            titulo.fontName = 'Helvetica-Bold'
            titulo.alignment = TA_CENTER
            tituloV = Paragraph(txtTitulo, titulo)
            elementos.append(tituloV)

            #Periodo
            elementos.append(Spacer(1,-15))# Quitandole espacio al periodo para subirlo un poco mas
            #txtPeriodo = u'%s hasta %s'%(memos[0].sent_at, memos[memos.count()-1].sent_at)
            txtPeriodo = 'Lista de memorándum desde %s/%s/%s hasta %s/%s/%s'%(memos[0].sent_at.day, memos[0].sent_at.month, memos[0].sent_at.year, memos[memos.count()-1].sent_at.day, memos[memos.count()-1].sent_at.month, memos[memos.count()-1].sent_at.year)
            periodo = Paragraph(txtPeriodo, styleF)
            elementos.append(periodo)

            num = 0
            tabla = []
            tabla.append(['NUM', 'REDACTADO', 'APROBADO POR', 'PARA', 'FECHA', 'ASUNTO']) # Encabezado de la Tabla.
            for memo in memos:
                num += 1
                jefe = jefe_dep(request)
                tabla.append([num, '%s \n(%s)' %(memo.sender.usuarios.persona.__unicode__(), memo.sender.usuarios.persona.cargo_principal.dependencia.departamento), '%s \n(%s)' %(jefe.usuarios.persona.__unicode__(), jefe.usuarios.persona.cargo_principal.dependencia.departamento), '%s \n(%s)' %(memo.recipient.usuarios.persona.__unicode__(), memo.recipient.usuarios.persona.cargo_principal.dependencia.departamento), '%s/%s/%s' %(memo.sent_at.day, memo.sent_at.month, memo.sent_at.year), memo.subject])

                t1 = Table(tabla, colWidths=('', '', '', '', '', ''))
                t1.setStyle(TableStyle(x))
            elementos.append(t1)#--> Para cargar la ultima tabla del reporte
            doc.build(elementos, canvasmaker=NumeroDePagina, onFirstPage=encabezado_constancia)
            return response  

            #libro_memos(request, lista_mensajes)
            #memo(request, lista_mensajes[0].id)




    c.update({'mensaje':mensaje})
    return render_to_response(template_name, c)
index = login_required(index)

PAGE_HEIGHT=29.7*cm
PAGE_WIDTH=21*cm

def libro_memos(request, memos):
    ''' Función para descarga de memorándums en PDF '''
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=Memorándum.pdf; pagesize=A4'

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
    # memo = Message.objects.filter(id=memos)

    txtTitulo = 'MEMORÁNDUM%s' %(salto)
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

    # Fin código de barras

    #doc.build(elementos, canvasmaker=NumeroDePagina, onFirstPage=encabezado_constancia)
    doc.build(elementos, canvasmaker=pieDePaginaConstancias, onFirstPage=encabezado_constancia)
    return response  

def memo(request, message_id):
    ''' Función para descarga de memorándums en PDF '''
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=Memorándum.pdf; pagesize=A4'

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

    txtTitulo = 'MEMORÁNDUM%s' %(salto)
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

    de = '<b>DE: </b> %s %s' %(memo.sender, salto)

    para = '' 
    memos = Message.objects.filter(codigo=memo.codigo)
    for memorandums in  memos:
        para = '%s, %s' %(memorandums.recipient, para)

    para = '<b>PARA: </b> %s %s' %(para, salto)

    para = '<b>ASUNTO: </b> %s %s' %(para, salto)

    memo_mes = fecha.NormalDate(memo.sent_at).monthName()
    memo_dia = fecha.NormalDate(memo.sent_at).dayOfWeekName()
    enviado = '<b>FECHA:</b> %s, %s de %s de %s a las %s:%s:%s %s'%(memo_dia, memo.sent_at.day, memo_mes, memo.sent_at.year, memo.sent_at.time().hour, memo.sent_at.time().minute, memo.sent_at.time().second, salto)

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

    Parrafo1 = Paragraph('%s'%(texto), parrafo)
    elementos.append(Parrafo1)
    elementos.append(Spacer(3,30))

    # Inicio código de barras
    codigoBarra_style = getSampleStyleSheet()
    codigoBarra = codigoBarra_style['Normal']
    codigoBarra.fontSize = 12
    codigoBarra.fontName = 'Courier'
    codigoBarra.alignment = TA_RIGHT

    st = createBarcodeDrawing('Code128',value = str(memo.codigo), barWidth= 0.040*cm, barHeight=0.500*cm, lquiet=11.950*cm)
    elementos.append(st)
    txtCodigoBarra = Paragraph(str(memo.codigo), codigoBarra)
    elementos.append(txtCodigoBarra)
    # Fin código de barras

    doc.build(elementos, canvasmaker=NumeroDePagina, onFirstPage=encabezado_constancia)
    return response  
memo = login_required(memo)

def encabezado_constancia(canvas, doc):
    canvas.saveState()
    canvas.drawImage(settings.STATIC_ROOT+'images/institucion.jpg', 2.0*cm, PAGE_HEIGHT-4.5*cm, width = 100, height = 38)
    canvas.setFont("Helvetica-Bold",10)
    canvas.drawCentredString(PAGE_WIDTH-9.5*cm, PAGE_HEIGHT-3.6*cm, 'REPÚBLICA BOLIVARIANA DE VENEZUELA')
    canvas.drawCentredString(PAGE_WIDTH-9.5*cm, PAGE_HEIGHT-4.0*cm, 'MINISTERIO DEL PODER POPULAR PARA LA EDUCACIÓN SUPERIOR')
    canvas.drawCentredString(PAGE_WIDTH-9.5*cm, PAGE_HEIGHT-4.4*cm, 'UNIVERSIDAD NACIONAL EXPERIMENTAL RÓMULO GALLEGOS')
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
            "%02d/%02d/%d   %02d:%02d:%02d    Página %d de %d" % (fechas.day,fechas.month,fechas.year, fechas.hour, fechas.minute, fechas.second, self._pageNumber, page_count))

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
            "%02d/%02d/%d   %02d:%02d:%02d    Página %d de %d" % (fechas.day,fechas.month,fechas.year, fechas.hour, fechas.minute, fechas.second, self._pageNumber, page_count))

def firma_actasIntegrales(canvas, doc):
    ##########-------------------- Pie de Pagina del reporte ###########
    canvas.saveState()
    canvas.setStrokeColor(black)
    canvas.setFont("Helvetica-BoldOblique",6.5)
    canvas.drawString(2.7*inch, 2.37*cm, 'Firma y Sello Decanato')
    canvas.drawString(4.35*inch, 2.37*cm, 'Firma y Sello Coordinación')
    #canvas.drawString(9.3*cm, 2.37*cm, 'Profesor:')
    #canvas.drawString(15*cm, 2.37*cm, u'Cédula:')
    #canvas.drawString(11.3*cm, 1.0*cm, 'Firma')
    #canvas.drawString(15*cm, 1.0*cm, 'Fecha')
    canvas.grid([2.3*inch, 4.1*inch, 5.8*inch], [0.23*inch, 1.06*inch])
    canvas.restoreState()
