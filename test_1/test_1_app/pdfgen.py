from django.core.management import setup_environ
from django.conf import settings
from django.views.generic.base import View
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib import colors
from reportlab.platypus import Paragraph, Table, TableStyle, Frame
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.widgets.markers import makeMarker
from reports import ClientReport
from django.http import HttpResponse
import datetime as d
import json
from django.core.management import setup_environ
from django.conf import settings
from django.core import mail

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

class BaseDocTemplate():
    """ The Base template class for the clients report"""

    def __init__(self, lt=None, gt=None, mac=None):
        self.lt = lt
        self.gt = gt
        self.mac = mac
        self.PAGE_HEIGHT=defaultPageSize[1]
        self.PAGE_WIDTH=defaultPageSize[0]
        self.styles = getSampleStyleSheet()
        self.p_style = ParagraphStyle(
            name='Normal',
            fontSize=18,
            textColor=colors.green,
            alignment=1
        )
        self.custom_heading = ParagraphStyle(
            name = 'Normal',
            fontSize=12,
            alignment=1
        )
        self.table_styleset = [
        ('FONT', (0, 0), (-1, -1), 'Helvetica'),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('BOX', (0, 0), (-1, 0), 0.25, colors.green),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ]
        self.styleN = self.styles["Normal"]
        self.styleH = self.styles["Heading1"]

        self.labels = []
        self.client_report = ClientReport(lt=self.lt, gt=self.gt, mac=self.mac)

    def add_frame(self, xpos, ypos, width, height, **kw):
        """  Add the frame to canvas"""
        print xpos, ypos, width, height, kw['showBoundary']
        frame = Frame(xpos, ypos, width, height, kw['showBoundary'])
        return frame

    def add_flowables(self, flowable, part):
        """ Add the paragraphs/spacers etc to the frame"""

        part.append(flowable)
        part.append(Spacer(1, 0.2*inch))
        return part

    def add_graphics(self, graphic_type, labels, data, part):
        if graphic_type == 'pie':
            if len(data) == 0:
                return part
            drawing = Drawing(120, 120)
            pc = Pie()
            pc.x = 90
            pc.y = 00
            pc.width = 90
            pc.height = 90
            pc.data = data
            pc.labels = labels
            pc.slices.strokeWidth=0.5
            drawing.add(pc)
            part.append(drawing)
            return part
        elif graphic_type == 'barchart':
            if len(data) == 0:
                return part
            drawing = Drawing(400, 200)
            yaxis = [[]]
            map(lambda x: yaxis[0].append(x), data)
            bc = VerticalBarChart()
            bc.x = 10*7*1.5 #customize this
            bc.y = 50
            bc.height = 125
            bc.width = 400 #customize this
            bc.data = yaxis
            bc.strokeColor = colors.black
            bc.barWidth = 2 #customize this
            bc.groupSpacing = 10 #customize this
            bc.valueAxis.valueMin = 0
            bc.valueAxis.valueMax = max(data)
            #bc.valueAxis.valueStep = 
            bc.categoryAxis.labels.boxAnchor = 'ne'
            bc.categoryAxis.labels.dx = 8
            bc.categoryAxis.labels.dy = -2
            bc.categoryAxis.labels.angle = 10
            bc.categoryAxis.categoryNames = labels
            drawing.add(bc)
            part.append(drawing)
            return part

    def create_table(self, data, column_spacing, style):
        """ Create the data matrix"""

        table = Table(data, column_spacing)
        table.setStyle(TableStyle(style))
        return table

    def consume_api(self, action, **kw):
        """ Call to report pdf apis"""

        if action == 'high_clients':
            self.data_usage_list = self.client_report.busiestClients()
            self.data_usage_list.sort(key = lambda row: row[1], reverse=True)
            self.table_fields = ['Client Mac', 'Data Usage (bytes)']
            self.data_usage_list.insert(0, self.table_fields)
            return self.data_usage_list

        elif action == 'clients_devtype':
            self.devtype_data = self.client_report.summaryClient()
            self.labels = map(lambda x: x[0], self.devtype_data)
            self.data = map(lambda x: x[1], self.devtype_data)
            return self.labels, self.data

        elif action == 'clients_by_ssid':
            self.ssid_clients = self.client_report.ssidClient()
            self.ssid_clients.sort(key = lambda row: row[1], reverse=True)
            self.table_fields = ['SSID' , 'No of Clients']
            self.ssid_clients.insert(0, self.table_fields)
            return self.ssid_clients

        elif action == 'clients_by_ssid_graphic':
            self.ssid_clients = self.client_report.ssidClient()
            self.labels = map(lambda x: x[0], self.ssid_clients)
            self.data = map(lambda x: x[1], self.ssid_clients)
            return self.labels, self.data

        elif action == 'unique_clients':
            self.unique_clients = self.client_report.uniqueClient()
            self.unique_clients.sort(key = lambda row: row[0], reverse=True)
            self.table_fields = ['Date', 'No of Clients']
            self.unique_clients.insert(0, self.table_fields)
            return self.unique_clients
        
class ApiBaseClass(View):
    """ Base class to be called for apis"""

    def __init__(self):
        """ Init for the base api"""

        self.w, self.h = letter
        self.frame_height, self.frame_width = 4*inch, 4*inch
        self.table_styleset = [
        ('FONT', (0, 0), (-1, -1), 'Helvetica'),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('BOX', (0, 0), (-1, 0), 0.25, colors.green),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ]

    def get(self, request):
        """ `get` call initiated for the apis"""

        response = HttpResponse(mimetype='application/pdf')
        response['Content-Disposition'] = 'filename="client_report.pdf"'

        offset  = d.datetime.utcnow() - d.timedelta(minutes=30)
        default_start = int((offset - d.datetime(1970, 1, 1)).total_seconds())
        default_end  = int((d.datetime.utcnow() - d.datetime(1970, 1, 1)).total_seconds())

        self.file_name = request.GET.get('file_name', 'client_report.pdf')
        self.gt = request.GET.get('start_time', 1383408852)
        self.lt = request.GET.get('end_time', 1393408852)

        c = canvas.Canvas(response)
        #c = canvas.Canvas(self.file_name, pagesize=letter, bottomup=1)

        doc = BaseDocTemplate(lt=self.lt, gt=self.gt)
        custom_heading = doc.custom_heading
        heading_style = doc.p_style

        frame = Frame(0, self.h-0.5*inch, self.w, 0.5*inch, showBoundary=1)
        part = []
        part = doc.add_flowables(Paragraph("<u>Clients Report</u>", 
                                heading_style), part
        )
        frame.addFromList(part, c)

        frame = Frame(0, self.h-(self.frame_height+0.5*inch), self.frame_width, 
                            self.frame_height, showBoundary=1
        )
        part = []
        part = doc.add_flowables(Paragraph("<u>Busiest Clients</u>", 
                                custom_heading), part
        )
        tab_data = doc.consume_api('high_clients')
        table = doc.create_table(tab_data, [1.5*inch, 1.5*inch], self.table_styleset)
        part = doc.add_flowables(table, part)
        frame.addFromList(part, c)

        frame = Frame(4*inch, self.h-(self.frame_height+0.5*inch), self.frame_width, 
                                self.frame_height, showBoundary=1
        )
        part = []
        part = doc.add_flowables(Paragraph("<u>Clients by Device Type</u>", 
                                custom_heading), part
        )
        labels, data = doc.consume_api('clients_devtype')
        part = doc.add_graphics('pie', labels, data, part)
        frame.addFromList(part, c)

        frame = Frame(0, 2.5*inch, self.frame_width, self.frame_height, showBoundary=1)
        part = []
        part = doc.add_flowables(Paragraph("<u>Clients by SSID</u>",
                                custom_heading), part
        )
        tab_data = doc.consume_api('clients_by_ssid')
        table = doc.create_table(tab_data, [1.5*inch, 1.5*inch], self.table_styleset)
        part = doc.add_flowables(table, part)
        frame.addFromList(part, c)

        frame = Frame(4*inch, 2.5*inch, self.frame_width, self.frame_height, showBoundary=1)
        part = []
        part = doc.add_flowables(Paragraph("<u>Unique Clients</u>",
                                custom_heading), part
        )
        tab_data = doc.consume_api('unique_clients')
        table = doc.create_table(tab_data, [1.5*inch], self.table_styleset)
        part = doc.add_flowables(table, part)
        frame.addFromList(part, c)

        c.showPage()

        frame = Frame(0, self.h-(self.frame_height+0.5*inch), self.frame_width + 4*inch, 
                            self.frame_height, showBoundary=1
        )
        part = []
        part = doc.add_flowables(Paragraph("<u>Clients by SSID</u>",
                                custom_heading), part
        )
        labels, data = doc.consume_api('clients_by_ssid_graphic')
        part = doc.add_graphics('barchart', labels, data, part)
        frame.addFromList(part, c)

        c.save()

        return response

def main_view(request):
    response = HttpResponse(mimetype='application/pdf')
    #response['Content-Disposition'] = 'attachment; filename="client_report.pdf"'
    response['Content-Disposition'] = 'filename="client_report.pdf"'

    buffer = StringIO()

    offset  = d.datetime.utcnow() - d.timedelta(minutes=30)
    default_start = int((offset - d.datetime(1970, 1, 1)).total_seconds())
    default_end  = int((d.datetime.utcnow() - d.datetime(1970, 1, 1)).total_seconds())

    post_data = json.loads(request.body)

    mac = post_data['mac']

    if 'time' in post_data and post_data['time']:
        gt = post_data['time'][0]
        lt = post_data['time'][1]
    else:
        gt = default_start
        lt = default_end

    title = None

    if 'reportTitle' in post_data and post_data['reportTitle']:
        title = post_data['reportTitle']

    file_name = 'demo_clients_report.pdf'   
    w, h = letter
    frame_height = 4*inch
    frame_width  = 4*inch
    table_styleset = [
        ('FONT', (0, 0), (-1, -1), 'Helvetica'),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('BOX', (0, 0), (-1, 0), 0.25, colors.green),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ]
    c = canvas.Canvas(buffer)

    doc = BaseDocTemplate(lt=lt, gt=gt, mac=mac)
    custom_heading = doc.custom_heading
    heading_style = doc.p_style

    """frame = doc.add_frame(0, h-(frame_height+0.5*inch), frame_width, 
                            frame_height, showBoundary=1
            )"""
    frame = Frame(0, h-0.5*inch, w, 0.5*inch, showBoundary=0)
    part = []
    part = doc.add_flowables(Paragraph("<u>%s</u>" % title, 
                            heading_style), part
    )
    frame.addFromList(part, c)


    frame = Frame(0, h-(frame_height+0.5*inch), frame_width, 
                        frame_height, showBoundary=0
    )

    part = []
    part = doc.add_flowables(Paragraph("<u>Busiest Clients</u>", 
                            custom_heading), part
    )
    tab_data = doc.consume_api('high_clients')
    table = doc.create_table(tab_data, [1.5*inch, 1.5*inch], table_styleset)
    part = doc.add_flowables(table, part)
    frame.addFromList(part, c)

    frame = Frame(4*inch, h-(frame_height+0.5*inch), frame_width, 
                            frame_height, showBoundary=0
    )
    part = []
    part = doc.add_flowables(Paragraph("<u>Clients by Device Type</u>", 
                            custom_heading), part
    )
    labels, data = doc.consume_api('clients_devtype')
    part = doc.add_graphics('pie', labels, data, part)
    frame.addFromList(part, c)

    frame = Frame(0, 2.5*inch, frame_width, frame_height, showBoundary=0)
    part = []
    part = doc.add_flowables(Paragraph("<u>Clients by SSID</u>",
                            custom_heading), part
    )
    tab_data = doc.consume_api('clients_by_ssid')
    table = doc.create_table(tab_data, [1.5*inch, 1.5*inch], table_styleset)
    part = doc.add_flowables(table, part)
    frame.addFromList(part, c)

    frame = Frame(4*inch, 2.5*inch, frame_width, frame_height, showBoundary=0)
    part = []
    part = doc.add_flowables(Paragraph("<u>Unique Clients</u>",
                            custom_heading), part
    )
    tab_data = doc.consume_api('unique_clients')
    table = doc.create_table(tab_data, [1.5*inch], table_styleset)
    part = doc.add_flowables(table, part)
    frame.addFromList(part, c)

    c.showPage()

    frame = Frame(0, h-(frame_height+0.5*inch), frame_width + 4*inch, 
                        frame_height, showBoundary=0
    )
    part = []
    part = doc.add_flowables(Paragraph("<u>Clients by SSID</u>",
                            custom_heading), part
    )
    labels, data = doc.consume_api('clients_by_ssid_graphic')
    part = doc.add_graphics('barchart', labels, data, part)
    frame.addFromList(part, c)

    c.save()

    pdf = buffer.getvalue()
    #send_mail(pdf)
    buffer.close()
    response.write(pdf)

    return response

def send_mail(pdf):
    connection = mail.get_connection()
    connection.open()

    email = mail.EmailMessage('Hey', 'This is the <strong>Clients Report</strong>', 
                        'pardeep.singh@vvdntech.com',
                        ['pardeep.singh@teramatrix.co'], connection=connection)
    email.content_subtype = "html"
    email.attach('client_report.pdf', pdf, 'application/pdf')
    email.send(fail_silently=False)

    connection.close()
    #return HttpResponse("Mail sent")

if __name__ == "__main__":
    main()
    #send_mail()

