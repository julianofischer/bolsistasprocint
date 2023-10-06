from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Image, Spacer, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus.tables import Table, TableStyle
from reportlab.lib import colors
from io import BytesIO
import datetime, os
from django.conf import settings
from .templatetags.reports_custom_tags import timedelta_hours

def __process_row_data(row_data):
    """
    Receives a dict with the row data and returns a list of lists with the data
    """
    styles = getSampleStyleSheet()
    header_style = ParagraphStyle(
        "centered", parent=styles["Normal"], alignment=1, fontName="Times-Bold", fontSize=10,
    ) 

    activity_style = ParagraphStyle(
        "left", parent=styles["Normal"], alignment=0, fontName="Times-Roman", fontSize=10,
    )

    data = []
    
    # add header
    data.append([Paragraph("Dia", header_style), Paragraph("Atividades desenvolvidas", header_style), Paragraph("Inicio", header_style), Paragraph("Fim", header_style), Paragraph("CH", header_style)])

    for row in row_data:
        data.append([row["dia"], Paragraph(row["atividade"], activity_style), row["inicio"], row["fim"], row["ch"]])

    return data


# Function to create the PDF
def generate_pdf(header_data, row_data):
    bolsista = header_data.get("bolsista", "bolsista")	
    funcao = header_data.get("funcao", "funcao")
    periodo = header_data.get("periodo", "periodo")
    telefone_institucional = header_data.get("telefone_institucional", "telefone_institucional")
    email = header_data.get("email", "email")

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5 * inch)

    # Define the styles for the document
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    centered_style = ParagraphStyle(
        "centered", parent=styles["Normal"], alignment=1, fontName="Times-Bold", fontSize=8,
    )  # Center-aligned style with Times Roman font

    # Create the content elements
    elements = []

    # Add an image at the top (replace 'image.jpg' with your image file)
    image_path = os.path.join(settings.BASE_DIR, "reports", "ifro.png")
    image = Image(image_path, width=7 * inch, height=.6 * inch)
    elements.append(image)
    elements.append(Spacer(1, 12))  # Add some space below the image

    # Add a centered title with Times Roman font
    title = "PROJETO CIDADES INTELIGENTES: UMA PROPOSTA DE IMPLANTAÇÃO PARA ARIQUEMES/RO"
    elements.append(Paragraph(title, centered_style))

    subtitle = "RELATÓRIO MENSAL DE ATIVIDADES DO COLABORADOR"
    elements.append(Paragraph(subtitle, centered_style))
    elements.append(Spacer(1, 12))  # Add some space below the image

    # Create the header table
    header_data = [
        ["Nome:", bolsista],
        ["Função:", funcao],
        ["Período:", periodo],
        ["Tel. Institucional:", telefone_institucional],
        ["E-mail:", email],
    ]
    
    total_width = 7 * inch  # Total available width
    column_widths = [total_width*.2, total_width*.8]  # Divide available width equally between the two columns
    header_table = Table(header_data, colWidths=column_widths)
    
    # Define table styles for signatures
    header_table_style = TableStyle(
        [
            ("ALIGN", (0, 0), (0, -1), "RIGHT"),  # Align first column (Name) to the right
            ("ALIGN", (1, 0), (-1, -1), "LEFT"),   # Align second column (Function) to the left
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
    activity_width = total_width * 0.7  # 80% of total width for "atividade desenvolvida"
    remaining_width = (total_width - activity_width) / 4  # Remaining width divided equally among other columns

    col_widths = [remaining_width] * 4  # List of column widths
    col_widths.insert(1, activity_width)  # Insert the activity column width at the second position

    # Define table styles with Times Roman font
    table_style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.darkgrey),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
            ("FONTNAME", (0, 0), (-1, 0), "Times-Roman"),  # Times Roman font for headers
            ("BOTTOMPADDING", (0, 0), (-1, 0), 0),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),  # Times Roman font for table content
            ("FONTSIZE", (0, 0), (-1, -1), 8),  # Font size 10 for table content
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
            ("FONTNAME", (0, 0), (-1, -1), "Times-Bold"),  # Times Roman font for table content
            ("FONTSIZE", (0, 0), (-1, -1), 10),  # Font size 10 for table content
        ]
    )
    footer_table.setStyle(footer_table_style)
    elements.append(footer_table)  # Add some space before the table

    # Add space for signatures
    elements.append(Spacer(1, 48))  # Add space for signatures (adjust as needed)
    
    # Create a table for signatures
    signature_data = [
        ["_" * 30, "_" * 30],
        [bolsista, "Vagner Schoaba"],
        ["Bolsista", "Coordenador"], 
    ]
    
    column_widths = [total_width / 2] * 2  # Divide available width equally between the two columns
    signature_table = Table(signature_data, colWidths=column_widths)
    
    # Define table styles for signatures
    signature_table_style = TableStyle(
        [
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, -1), "Times-Roman"),  # Times Roman font for signatures
            ("FONTSIZE", (0, 0), (-1, -1), 10),  # Font size 10 for signatures
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]
    )
    
    signature_table.setStyle(signature_table_style)
    elements.append(signature_table)  # Add the signature table to the document

    # Build the PDF document
    doc.build(elements)
    pdf_file = buffer.getvalue()
    buffer.close()
    return pdf_file

# generate_pdf("7.pdf", {}, {"dia": "01", "atividade": "atividade", "inicio": "08:00", "fim": "12:00", "ch": "4"})