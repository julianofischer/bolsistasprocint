from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Image, Spacer, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus.tables import Table, TableStyle
from reportlab.lib import colors
from io import BytesIO
import datetime, os
from django.conf import settings
from django.utils import timezone
from .templatetags.reports_custom_tags import timedelta_hours

import qrcode


FOOTER_TEMPLATE = "Este documento foi assinado digitalmente e a sua autenticidade pode ser conferida no site {} ou através do QR Code ao lado"

def __process_row_data(row_data):
    """
    Receives a dict with the row data and returns a list of lists with the data
    """
    styles = getSampleStyleSheet()
    header_style = ParagraphStyle(
        "centered",
        parent=styles["Normal"],
        alignment=1,
        fontName="Times-Bold",
        fontSize=10,
    )

    activity_style = ParagraphStyle(
        "left",
        parent=styles["Normal"],
        alignment=0,
        fontName="Times-Roman",
        fontSize=10,
    )

    data = []

    # add header
    data.append(
        [
            Paragraph("Dia", header_style),
            Paragraph("Atividades desenvolvidas", header_style),
            Paragraph("Inicio", header_style),
            Paragraph("Fim", header_style),
            Paragraph("CH", header_style),
        ]
    )

    for row in row_data:
        data.append(
            [
                row["dia"],
                Paragraph(row["atividade"], activity_style),
                row["inicio"],
                row["fim"],
                row["ch"],
            ]
        )

    return data


def _header_footer(canvas, doc):
    # Save the state of our canvas so we can draw on it
    canvas.saveState()
    styles = getSampleStyleSheet()

    # Header
    # header = Paragraph('This is a multi-line header.  It goes on every page.   ' * 5, styles['Normal'])
    # w, h = header.wrap(doc.width, doc.topMargin)
    # header.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - h)

    # Footer
    # Draw a line at the bottom of the header
    canvas.line(
        doc.leftMargin,
        doc.height + doc.topMargin,
        doc.width + doc.leftMargin,
        doc.height + doc.topMargin,
    )

    footer_style = ParagraphStyle(
        'CustomFooter',
        parent=styles['Normal'],
        # borderColor=colors.black,
        # borderWidth=.1,
        fontSize=8,
    )

    footer_text = FOOTER_TEMPLATE.format(settings.BASE_URL)
    footer = Paragraph(
        footer_text, footer_style
    )
    w, h = footer.wrap(doc.width, doc.bottomMargin)
    
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data('Some data')
    qr.make(fit=True)

    qr_image = qr.make_image(fill_color="black", back_color="white")
    qr_img_bytes = BytesIO()
    qr_image.save(qr_img_bytes, format='PNG')

    qr_image_obj = Image(qr_img_bytes, width=75, height=75)
    qr_image_obj.drawOn(canvas, doc.leftMargin - 40, doc.bottomMargin - 60)

    footer.drawOn(canvas, doc.leftMargin + 35, doc.bottomMargin - 30)

    # Draw a line at the top of the footer
    canvas.line(doc.leftMargin - 40, doc.bottomMargin + 8, doc.width + doc.leftMargin + 40, doc.bottomMargin + 8)
    

    # Release the canvas
    canvas.restoreState()


def onLaterPages(canvas, doc):
    # Draw a rectangle at the bottom of the page
    canvas.saveState()
    canvas.rect(50, 50, doc.width, 50)  # Adjust the position and size as needed
    canvas.restoreState()


def _extract_header_data(report):
    header_data = {}
    header_data["bolsista"] = report.user.name
    header_data["funcao"] = report.user.role
    header_data["periodo"] = report.formatted_ref_month()
    header_data["telefone"] = report.user.phone_number or ""
    header_data["email"] = report.user.email
    return header_data

def _extract_row_data(report):
    row_data = []
    entries = report.entries.all()
    for entry in entries:
        row_data.append(
            {
                "dia": entry.date.day,
                "atividade": entry.description,
                "inicio": entry.init_hour,
                "fim": entry.end_hour,
                "ch": entry.hours,
            }
        )
    return row_data

def _extract_signatures(report):
    signatures = {}
    sign_objects = report.signatures.all()
    signatures["bolsista"] = sign_objects.filter(user=report.user).first()
    # a assinatura do coordenador é a primeira que não é do bolsista
    signatures["coordenador"] = sign_objects.filter(user__is_staff=True).exclude(user=report.user).first()
    return signatures


# Function to create the PDF
def generate_pdf(report):
    header_data = _extract_header_data(report)
    row_data = _extract_row_data(report)
    assinaturas = _extract_signatures(report)

    bolsista = header_data.get("bolsista", "bolsista")
    funcao = header_data.get("funcao", "funcao")
    periodo = header_data.get("periodo", "periodo")
    telefone = header_data.get("telefone", "telefone")
    email = header_data.get("email", "email")

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=0.5 * inch,
        onFirstPage=_header_footer,
        onLaterPages=_header_footer,
    )

    # Define the styles for the document
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    centered_style = ParagraphStyle(
        "centered",
        parent=styles["Normal"],
        alignment=1,
        fontName="Times-Bold",
        fontSize=8,
    )  # Center-aligned style with Times Roman font

    # Create the content elements
    elements = []

    # Add an image at the top (replace 'image.jpg' with your image file)
    image_path = os.path.join(settings.BASE_DIR, "reports", "ifro.png")
    image = Image(image_path, width=7 * inch, height=0.6 * inch)
    elements.append(image)
    elements.append(Spacer(1, 12))  # Add some space below the image

    # Add a centered title with Times Roman font
    title = (
        "PROJETO CIDADES INTELIGENTES: UMA PROPOSTA DE IMPLANTAÇÃO PARA ARIQUEMES/RO"
    )
    elements.append(Paragraph(title, centered_style))

    subtitle = "RELATÓRIO MENSAL DE ATIVIDADES DO COLABORADOR"
    elements.append(Paragraph(subtitle, centered_style))
    elements.append(Spacer(1, 12))  # Add some space below the image

    # Create the header table
    header_data = [
        ["Nome:", bolsista],
        ["Função:", funcao],
        ["Período:", periodo],
        ["Telefone:", telefone],
        ["E-mail:", email],
    ]

    total_width = 7 * inch  # Total available width
    column_widths = [
        total_width * 0.2,
        total_width * 0.8,
    ]  # Divide available width equally between the two columns
    header_table = Table(header_data, colWidths=column_widths)

    # Define table styles for signatures
    header_table_style = TableStyle(
        [
            (
                "ALIGN",
                (0, 0),
                (0, -1),
                "RIGHT",
            ),  # Align first column (Name) to the right
            (
                "ALIGN",
                (1, 0),
                (-1, -1),
                "LEFT",
            ),  # Align second column (Function) to the left
            ("FONTNAME", (0, 0), (0, -1), "Times-Bold"),
            ("FONTNAME", (1, 0), (-1, -1), "Times-Roman"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),  # Font size 10 for signatures
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]
    )

    header_table.setStyle(header_table_style)
    elements.append(header_table)  # Add the signature table to the document

    data = __process_row_data(row_data)

    # Calculate column widths
    total_width = 7 * inch  # Total available width
    activity_width = (
        total_width * 0.7
    )  # 80% of total width for "atividade desenvolvida"
    remaining_width = (
        total_width - activity_width
    ) / 4  # Remaining width divided equally among other columns

    col_widths = [remaining_width] * 4  # List of column widths
    col_widths.insert(
        1, activity_width
    )  # Insert the activity column width at the second position

    # Define table styles with Times Roman font
    table_style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.darkgrey),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Times-Roman",
            ),  # Times Roman font for headers
            ("BOTTOMPADDING", (0, 0), (-1, 0), 0),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            (
                "FONTNAME",
                (0, 1),
                (-1, -1),
                "Times-Roman",
            ),  # Times Roman font for table content
            ("FONTSIZE", (0, 0), (-1, -1), 8),  # Font size 10 for table content
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),  # vertical alignment
        ]
    )

    # alternate row colors
    for each in range(1, len(data)):
        if each % 2 == 0:
            bg_color = colors.HexColor("#FFFFFF")
        else:
            bg_color = colors.HexColor("#ECECEC")
        table_style.add("BACKGROUND", (0, each), (-1, each), bg_color)

    # Create the table with the specified column widths and apply the styles
    table = Table(data, colWidths=col_widths)
    table.setStyle(table_style)

    # Add the table to the document
    elements.append(Spacer(1, 12))  # Add some space before the table
    elements.append(table)

    total_horas = sum([row["ch"] for row in row_data], datetime.timedelta())
    total_horas = timedelta_hours(total_horas)

    footer_table = Table([[f"Total de horas: {total_horas}"]], colWidths=[total_width])
    footer_table_style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.darkgrey),
            ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            (
                "FONTNAME",
                (0, 0),
                (-1, -1),
                "Times-Bold",
            ),  # Times Roman font for table content
            ("FONTSIZE", (0, 0), (-1, -1), 10),  # Font size 10 for table content
        ]
    )
    footer_table.setStyle(footer_table_style)
    elements.append(footer_table)  # Add some space before the table
    # Add space for signatures
    elements.append(Spacer(1, 48))  # Add space for signatures (adjust as needed)

    # student signature
    # image_path = os.path.join(settings.BASE_DIR, "static", "assets", "certificate.png")
    # img = Image(image_path, width=200, height=100)
    # a = f'<img src="{img}" width="200" height="100"/>'
    styles = getSampleStyleSheet()
    signature_style = ParagraphStyle(
        "centered",
        parent=styles["Code"],
        splitLongWords=1,
        borderColor=colors.black,
        borderWidth=1,
        backColor=colors.whitesmoke,
        borderPadding=(5, 5, 5, 5),
        leftIndent=0,
    )
    
    table_student_signature = ""
    if "bolsista" in assinaturas and assinaturas.get("bolsista", False):
        assinatura = assinaturas.get("bolsista")
        student = assinatura.user.name
        # Converta o objeto DateTimeField para a timezone desejada (opcional)
        timestamp = timezone.localtime(assinatura.signed_at)
        # Formate a data e hora no estilo desejado
        dt_fmt = "%d de %B de %Y às %H:%M:%S"
        data_formatada = timestamp.strftime(dt_fmt)

        student_signature = Paragraph(
            f"Assinado digitalmente por {student} em {data_formatada}",
            signature_style,
        )
        table_student_signature = Table(
            [[student_signature]], 200
        )  # Set the maximum width to 200
    
    table_coordinator_signature = ""
    if "coordenador" in assinaturas and assinaturas.get("coordenador", False):
        coordinator = assinaturas.get("coordenador").user.name
        coordinator_signature = Paragraph(
            f"Assinado digitalmente por {coordinator} em 01/01/2021 às 12:00:00",
            signature_style,
        )
        table_coordinator_signature = Table(
            [[coordinator_signature]], 200
        )

    # TODO: GERAR QR CODE IMAGEM TEMPORARIAMENTE
    # E INSERIR INLINE NO PDF

    # Create a table for signatures
    signature_data = [
        [table_student_signature, table_coordinator_signature],
        ["_" * 30, "_" * 30],
        [bolsista, assinaturas.get("coordenador", "")],
        ["Bolsista", "Coordenador"],
    ]

    column_widths = [
        total_width / 2
    ] * 2  # Divide available width equally between the two columns
    signature_table = Table(signature_data, colWidths=column_widths)

    # Define table styles for signatures
    signature_table_style = TableStyle(
        [
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            (
                "FONTNAME",
                (0, 0),
                (-1, -1),
                "Times-Roman",
            ),  # Times Roman font for signatures
            ("FONTSIZE", (0, 0), (-1, -1), 10),  # Font size 10 for signatures
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]
    )

    signature_table.setStyle(signature_table_style)
    elements.append(signature_table)  # Add the signature table to the document

    # Build the PDF document
    if report.signed:
        doc.build(elements, onFirstPage=_header_footer, onLaterPages=_header_footer)
    else:
        doc.build(elements)

    pdf_file = buffer.getvalue()
    buffer.close()
    return pdf_file
