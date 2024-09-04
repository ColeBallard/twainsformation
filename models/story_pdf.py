import os
import datetime

from werkzeug.utils import secure_filename
from fpdf import FPDF

class StoryPDF:
    def __init__(self):
        self.title = ''
        self.text = ''

        # Define constants for PDF creation
        self.MARGIN = 20  # Margin in mm
        self.PAGE_WIDTH = 170  # Standard A4 width in mm
        self.PAGE_HEIGHT = 297  # Standard A4 height in mm
        self.TITLE_FONT = 'Times'
        self.TITLE_FONT_SIZE = 24  # Font size for title
        self.BODY_FONT = 'Times'
        self.BODY_FONT_SIZE = 12  # Font size for body text
        self.INDENT = 10  # Indentation for paragraphs in mm
        self.LINE_HEIGHT = 8  # Line height for body text in mm
        self.PDF_DIR = '/tmp/transformed_books'  # Directory for saving PDFs

    def sanitizeText(self, text):
        # Replace specific non-Latin-1 characters with their Latin-1 equivalents or remove them
        return text.replace('\u2013', '-').replace('\u2014', '--').replace('\u2018', "'").replace('\u2019', "'").replace('\u2026', '...')  # Add more replacements as needed

    def create(self, title, text):
        self.title = title
        self.text = text

        pdf = FPDF()

        text = self.sanitizeText(self.text)

        pdf.set_margins(self.MARGIN, self.MARGIN, self.MARGIN)  # Set larger margins (20mm on each side)
        pdf.add_page()

        # Set font for the title to Times New Roman, bold, size 24
        pdf.set_font(self.TITLE_FONT, 'B', self.TITLE_FONT_SIZE)
        pdf_w = self.PAGE_WIDTH  # Adjust width for the new margins
        title_w = pdf.get_string_width(self.title) + 6
        title_x = (pdf_w - title_w) / 2 + self.MARGIN  # Adjust for left margin
        title_y = (self.PAGE_HEIGHT - self.INDENT) / 4  # Place title roughly in the upper third
        
        pdf.set_xy(title_x, title_y)
        pdf.cell(title_w, self.INDENT, self.title, 0, 1, 'C')
        
        pdf.add_page()
        pdf.set_font(self.BODY_FONT, size=self.BODY_FONT_SIZE)
        
        # Process each paragraph for indentation and reduced line spacing
        indent = self.INDENT  # Indentation for paragraphs in mm
        line_height = self.LINE_HEIGHT  # Adjust line height for tighter spacing
        paragraphs = text.split('\n')
        
        for paragraph in paragraphs:
            if paragraph.strip():  # Check if paragraph is not just whitespace
                pdf.set_x(pdf.l_margin + indent)  # Apply indentation
                pdf.multi_cell(0, line_height, paragraph)
            else:
                pdf.ln(6)  # Add a blank line for paragraph spacing

        # Define a temporary directory within /tmp for PDFs
        pdf_directory = self.PDF_DIR  # Adjusted to /tmp for compatibility
        
        # Check if the directory exists, and create it if it doesn't
        if not os.path.exists(pdf_directory):
            os.makedirs(pdf_directory)

        # Secure the title and replace spaces with underscores
        safe_title = secure_filename(self.title).replace(' ', '_')

        # Generate a timestamp string
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        # Append the timestamp to the safe_title
        safe_title = f"{safe_title}_{timestamp}.pdf"

        pdf_full_path = os.path.join(pdf_directory, safe_title)

        # Save the PDF file
        pdf.output(pdf_full_path)

        return pdf_full_path