"""
Custom page templates for PDF generation with headers and footers.
"""

from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import PageTemplate, Frame, BaseDocTemplate
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """
    Custom canvas that adds page numbers and headers/footers.
    """
    
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []
        self.doc_title = ""
        self.current_section = ""
        self.show_header = True
        self.show_footer = True
        self.show_page_numbers = True
        self.include_watermark = False
        self.watermark_text = ""
        self.watermark_opacity = 0.1
        
    def showPage(self):
        """
        Save the current page state before showing it.
        """
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()
        
    def save(self):
        """
        Add page numbers and headers/footers to all pages.
        """
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)
        
    def draw_page_decorations(self, page_count):
        """
        Draw headers, footers, and page numbers.
        
        Args:
            page_count: Total number of pages in the document
        """
        page_num = self._pageNumber
        
        # Skip decorations on cover page (page 1)
        if page_num == 1:
            return
            
        # Add watermark if enabled
        if self.include_watermark and self.watermark_text:
            self.saveState()
            self.setFillColor(colors.HexColor("#cccccc"))
            self.setFillAlpha(self.watermark_opacity)
            self.setFont("Helvetica", 60)
            self.translate(4.25 * inch, 5.5 * inch)
            self.rotate(45)
            self.drawCentredString(0, 0, self.watermark_text)
            self.restoreState()
        
        # Draw header
        if self.show_header:
            self.saveState()
            self.setFont("Helvetica", 9)
            self.setFillColor(colors.HexColor("#64748b"))
            
            # Left side: Section title (if available)
            if self.current_section:
                self.drawString(0.75 * inch, 10.75 * inch, self.current_section[:60])
            
            # Right side: Page number
            if self.show_page_numbers:
                page_text = f"Page {page_num}"
                self.drawRightString(7.75 * inch, 10.75 * inch, page_text)
            
            # Header line
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(0.75 * inch, 10.65 * inch, 7.75 * inch, 10.65 * inch)
            
            self.restoreState()
        
        # Draw footer
        if self.show_footer:
            self.saveState()
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#94a3b8"))
            
            # Left side: Document title
            if self.doc_title:
                self.drawString(0.75 * inch, 0.5 * inch, self.doc_title[:60])
            
            # Right side: Generation date
            date_text = datetime.now().strftime("%B %d, %Y")
            self.drawRightString(7.75 * inch, 0.5 * inch, date_text)
            
            # Footer line
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(0.75 * inch, 0.6 * inch, 7.75 * inch, 0.6 * inch)
            
            self.restoreState()


def create_page_templates(doc: BaseDocTemplate, settings) -> list:
    """
    Create page templates with headers and footers.
    
    Args:
        doc: ReportLab document template
        settings: PDF header/footer settings
        
    Returns:
        List of PageTemplate objects
    """
    # Standard page template with header and footer
    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id='normal'
    )
    
    templates = [
        PageTemplate(id='standard', frames=[frame])
    ]
    
    return templates
