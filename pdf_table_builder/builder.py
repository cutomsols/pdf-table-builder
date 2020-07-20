import os
from io import BytesIO

from PIL import Image as pilim
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, Image
from reportlab.platypus import Frame, PageTemplate
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.platypus import Spacer

from emergdept.pdf_table_builder.consts import *

styles = getSampleStyleSheet()
styleN = styles['Normal']
styleH = styles['Heading1']

DESIRED_PHOTO_WIDTH = A4[0] - 100
DESIRED_PHOTO_HEIGHT = A4[1] / 2 - 170

BASIC_MARGIN = 30
LEFT_MARGIN = BASIC_MARGIN
RIGHT_MARGIN = BASIC_MARGIN
TOP_MARGIN = BASIC_MARGIN
BOTTOM_MARGIN = BASIC_MARGIN
BODY_FONT_SIZE = 8
PAGE_WIDTH = 530
PAGE_HEIGHT = 750
LINE_Y = 730
TABLE_FINAL_COLS = ['date']
BODY_STYLE = None
USER_IS_CLIENT = None

WATERMARK = None
LOGO_PATH = None
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def build_pdf(data, logo_path=None, watermark=None, images_data=None):
    global WATERMARK
    global LOGO_PATH
    global BODY_STYLE

    LOGO_PATH = logo_path
    WATERMARK = watermark
    BODY_STYLE = get_body_style()

    pdf_buffer = BytesIO()
    pdf = BaseDocTemplate(pdf_buffer, pagesize=A4)
    frame = Frame(LEFT_MARGIN, BOTTOM_MARGIN, PAGE_WIDTH, 687, showBoundary=1)
    template = PageTemplate(id='all_pages', frames=frame, onPage=header_and_footer)
    pdf.addPageTemplates([template])

    images_before_table = []
    images_after_table = []
    for img_path, img_pos in images_data.items():
        if img_pos == IMAGE_DOC_POSITION_BEFORE_TABLE:
            images_before_table.append(img_path)
        elif img_pos == IMAGE_DOC_POSITION_AFTER_TABLE:
            images_after_table.append(img_path)

    story = []

    for img_path in images_before_table:
        story.extend([
            Spacer(10, 10),
            Image(img_path, width=100, height=100),
            Spacer(10, 10)
        ])

    story.append(pfd_table_builder(data))

    for img_path in images_after_table:
        story.extend([
            Spacer(10, 10),
            Image(img_path, width=100, height=100),
            Spacer(10, 10)
        ])
    pdf.build(story)
    pdf_value = pdf_buffer.getvalue()
    pdf_buffer.close()
    return pdf_value


def get_img(img_path):
    # buff1 = BytesIO()
    # img = pilim.open(img_path)
    # print('img_path:', img_path, img.size[0], img.size[1])
    # door_out_img = Image(img_path, width=2 * inch, height=2 * inch)

    return '''<para autoLeading="off" fontSize=12>This &lt;img/&gt; <img
src="{0}" valign="top" width="{1}" height="{2}"/> </para>'''.format(img_path, 100, 100)


def pfd_table_builder(data):
    """
    Example usage:

    data = [
        {
            TABLE_ROW_TYPE: TABLE_ROW_TYPE_TITLE,
            TABLE_ROW_TITLE: '<font size=10>{}</font>'.format(datetime.date.today().strftime("%d/%m/%Y"))
        },
        {TABLE_ROW_TYPE: TABLE_ROW_TYPE_SPACER},
        {
            TABLE_ROW_TYPE: TABLE_ROW_TYPE_TITLE,
            TABLE_ROW_TITLE: 'Outside Colors:'
        },
        {
            TABLE_ROW_TYPE: TABLE_ROW_TYPE_REGULAR,
            TABLE_ROW_DATA: [
                {
                    TABLE_COLUMN_CONTENT: 'Panel color outside:',
                    # or TABLE_COLUMN_ALIGN_CENTER, TABLE_COLUMN_ALIGN_RIGHT, TABLE_COLUMN_ALIGN_JUSTIFY
                },
                {TABLE_COLUMN_CONTENT: '7012 Matt'},
                {
                    TABLE_COLUMN_CONTENT: '$100',
                    TABLE_COLUMN_ALIGN: TABLE_COLUMN_ALIGN_RIGHT,
                }
            ]
        },
    ]

    table = pfd_table_builder(data)

    :param data:
    :return: A reportlab table instance
    """
    table_data = []
    body_style = get_body_style()
    for row in data:
        if row.get(TABLE_ROW_TYPE) == TABLE_ROW_TYPE_TITLE:
            TABLE_FINAL_COLS.append('title')
            table_data.append([
                Paragraph('{}'.format(row.get(TABLE_ROW_DATA)), body_style)
            ])
        if row.get(TABLE_ROW_TYPE) == TABLE_ROW_TYPE_SPACER:
            TABLE_FINAL_COLS.append('spacer')
            table_data.append([
                Spacer(*row.get(TABLE_ROW_DATA, (1, 1)))
            ])
        if row.get(TABLE_ROW_TYPE) == TABLE_ROW_TYPE_REGULAR:
            TABLE_FINAL_COLS.append('v')
            column = []
            for col_dict in row.get(TABLE_ROW_DATA):
                # Get paragraph specific style (only alignment for now)
                style = BODY_STYLE
                column_align = col_dict.get(TABLE_COLUMN_ALIGN)
                if column_align:
                    style = get_body_style()
                    style.alignment = TA_CENTER if (column_align == TABLE_COLUMN_ALIGN_CENTER) else TA_RIGHT if (
                            column_align == TABLE_COLUMN_ALIGN_RIGHT) else TA_JUSTIFY if (
                            column_align == TABLE_COLUMN_ALIGN_JUSTIFY) else TA_LEFT
                column.append([
                    Paragraph('{}'.format(col_dict.get(TABLE_COLUMN_CONTENT, 'N/A')), style)
                ])
            table_data.append(column)

    table_styles_list = []
    table_row_date = colors.HexColor('#d9d9d9')
    table_row_color_title = colors.HexColor('#bdbdbd')
    table_row_color_white = colors.HexColor('#ffffff')
    table_row_color_col_dark = colors.HexColor('#ededed')
    ctr = 0
    for i, td in enumerate(table_data):
        if i == 0:  # First col -> Date
            table_styles_list.append(('BACKGROUND', (0, i), (2, i), table_row_date))
        elif TABLE_FINAL_COLS[i] == 'title':
            table_styles_list.append(('BACKGROUND', (0, i), (2, i), table_row_color_title))
        elif TABLE_FINAL_COLS[i] == 'spacer':
            table_styles_list.append(('BACKGROUND', (0, i), (2, i), table_row_color_white))
        else:  # item
            if ctr % 2 == 0:
                table_styles_list.append(('BACKGROUND', (0, i), (2, i), table_row_color_col_dark))
            else:
                table_styles_list.append(('BACKGROUND', (0, i), (2, i), table_row_color_white))
            ctr += 1

    t = Table(table_data)
    t.setStyle(TableStyle(table_styles_list))
    return t


def header_and_footer(canvas, pdf):
    # LOGO
    print('LOGO_PATH', LOGO_PATH)
    if LOGO_PATH:
        im = pilim.open(LOGO_PATH)
        pil_img = ImageReader(im)
        canvas.drawImage(pil_img, 350, PAGE_HEIGHT, width=210, height=70, mask='auto')

    canvas.line(BASIC_MARGIN, LINE_Y, PAGE_WIDTH + BASIC_MARGIN, LINE_Y)

    # ----------------------- FOOTER ----------------------- #
    canvas.setFont('Helvetica-Bold', 8)
    # page number
    page_number_text = "%d" % pdf.page
    canvas.drawCentredString(295, 8, '-' + page_number_text + '-')
    # watermark
    if WATERMARK:
        canvas.drawCentredString(507, 8, WATERMARK)

    canvas.line(BASIC_MARGIN, 20, PAGE_WIDTH + BASIC_MARGIN, 20)


def get_body_style():
    sample_style_sheet = getSampleStyleSheet()
    body_style = sample_style_sheet['BodyText']
    body_style.fontSize = BODY_FONT_SIZE
    print('__location__', __location__)
    pdfmetrics.registerFont(TTFont('NotoSans', os.path.join(__location__, 'fonts/NotoSans-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('NotoSansBold', os.path.join(__location__, 'fonts/NotoSans-Bold.ttf')))
    body_style.fontName = 'NotoSans'
    return body_style
