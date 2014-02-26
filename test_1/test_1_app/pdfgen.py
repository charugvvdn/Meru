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


class BaseDocTemplate():
    """ The Base template class for the clients report"""

    def __init__(self, lt=None, gt=None):
        self.lt = lt
        self.gt = gt
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
        self.client_report = ClientReport(lt=self.lt, gt=self.gt)

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
            bc.barWidth = 5 #customize this
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
            self.labels = map(lambda x: x[0], self.devtype_data)
            self.data = map(lambda x: x[1], self.devtype_data)
            return self.labels, self.data

        elif action == 'unique_clients':
            self.unique_clients = self.client_report.uniqueClient()
            self.table_fields = ['Mac']
            self.unique_clients.insert(0, self.table_fields)
            return self.unique_clients
        


def main():
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
    c = canvas.Canvas(file_name, pagesize=letter, bottomup=1)

    doc = BaseDocTemplate(lt=1392323231, gt=1388787871)
    custom_heading = doc.custom_heading
    heading_style = doc.p_style

    '''frame = doc.add_frame(0, h-(frame_height+0.5*inch), frame_width, 
                            frame_height, showBoundary=1
            )'''
    frame = Frame(0, h-0.5*inch, w, 0.5*inch, showBoundary=1)
    part = []
    part = doc.add_flowables(Paragraph("<u>Clients Report</u>", 
                            heading_style), part
    )
    frame.addFromList(part, c)

    frame = Frame(0, h-(frame_height+0.5*inch), frame_width, 
                        frame_height, showBoundary=1
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
                            frame_height, showBoundary=1
    )
    part = []
    part = doc.add_flowables(Paragraph("<u>Clients by Device Type</u>", 
                            custom_heading), part
    )
    labels, data = doc.consume_api('clients_devtype')
    part = doc.add_graphics('pie', labels, data, part)
    frame.addFromList(part, c)

    frame = Frame(0, 2.5*inch, frame_width, frame_height, showBoundary=1)
    part = []
    part = doc.add_flowables(Paragraph("<u>Clients by SSID</u>",
                            custom_heading), part
    )
    tab_data = doc.consume_api('clients_by_ssid')
    table = doc.create_table(tab_data, [1.5*inch, 1.5*inch], table_styleset)
    part = doc.add_flowables(table, part)
    frame.addFromList(part, c)

    frame = Frame(4*inch, 2.5*inch, frame_width, frame_height, showBoundary=1)
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
                        frame_height, showBoundary=1
    )
    part = []
    part = doc.add_flowables(Paragraph("<u>Clients by SSID</u>",
                            custom_heading), part
    )
    labels, data = doc.consume_api('clients_by_ssid_graphic')
    part = doc.add_graphics('barchart', labels, data, part)
    frame.addFromList(part, c)

    c.save()

if __name__ == "__main__":
    main()
