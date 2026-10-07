# pdf_generator.py - Enhanced Black Theme PDF with Avenir Typography
import os
import logging
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak, 
                                 Frame, PageTemplate, Table, TableStyle, HRFlowable)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY, TA_CENTER, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, black, white, blue
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import simpleSplit
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def register_avenir_fonts():
    """Register Avenir fonts if available, fallback to Helvetica"""
    try:
        # Try to register Avenir Next LT Pro
        pdfmetrics.registerFont(TTFont('Avenir', 'AvenirNextLTPro-Regular.ttf'))
        pdfmetrics.registerFont(TTFont('Avenir-Bold', 'AvenirNextLTPro-Bold.ttf'))
        pdfmetrics.registerFont(TTFont('Avenir-Italic', 'AvenirNextLTPro-It.ttf'))
        pdfmetrics.registerFont(TTFont('Avenir-Medium', 'AvenirNextLTPro-Medium.ttf'))
        return 'Avenir'
    except:
        # Fallback to Helvetica
        logger.warning("Avenir fonts not found, using Helvetica")
        return 'Helvetica'

def create_minimalist_line(width=0.5, color=black, space_before=5, space_after=5):
    """Create a minimalist horizontal line"""
    return [Spacer(1, space_before), 
            HRFlowable(width="100%", thickness=width, color=color, 
                      spaceBefore=0, spaceAfter=0, 
                      hAlign='CENTER', vAlign='BOTTOM'),
            Spacer(1, space_after)]

def create_hyperlink(url, text, color=HexColor('#007AFF')):
    """
    Create a clickable hyperlink for PDF
    Returns formatted HTML string for use in Paragraph
    """
    # Clean and validate URL
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    
    # Escape special characters for HTML
    url = url.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    # Create hyperlink with blue color
    hex_color = color.hexval() if hasattr(color, 'hexval') else '#007AFF'
    return f'<a href="{url}" color="{hex_color}"><u>{text}</u></a>'

def get_domain_from_url(url):
    """Extract domain name from URL for display"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '').split('.')[0].upper()
        return domain if domain else "SOURCE"
    except:
        return "SOURCE"

def create_unified_pdf_with_e7(all_data, output_dir=None):
    """
    Create enhanced minimalist black & white PDF with Avenir typography
    Premium black theme design with clean aesthetics
    """
    from config import OUTPUT_DIR
    from utils import get_time_ago
    
    if output_dir is None:
        output_dir = OUTPUT_DIR
    
    filename = f"MS HOLDINGS_DAILY MARKET REPORT_FOR-{datetime.now().strftime('%d-%m-%Y')}.pdf"
    filepath = os.path.join(output_dir, filename)
    os.makedirs(output_dir, exist_ok=True)
    
    # Register fonts
    font_family = register_avenir_fonts()
    font_bold = f'{font_family}-Bold' if font_family == 'Avenir' else 'Helvetica-Bold'
    font_italic = f'{font_family}-Italic' if font_family == 'Avenir' else 'Helvetica-Oblique'
    font_medium = f'{font_family}-Medium' if font_family == 'Avenir' else 'Helvetica'
    
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        topMargin=0.7*inch,
        bottomMargin=0.6*inch,
        leftMargin=0.6*inch,
        rightMargin=0.6*inch,
        showBoundary=0
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # ===== PREMIUM BLACK COLOR PALETTE =====
    PURE_BLACK = HexColor('#000000')
    RICH_BLACK = HexColor('#000000')
    DEEP_CHARCOAL = HexColor('#000000')
    DARK_SLATE = HexColor('#000000')
    MEDIUM_SLATE = HexColor('#000000')
    LIGHT_SLATE = HexColor('#000000')
    SILVER = HexColor('#000000')
    PURE_WHITE = white
    HYPERLINK_BLUE = HexColor('#007AFF')  # Apple-style blue for links
    LINK_HOVER_BLUE = HexColor('#0056CC')  # Slightly darker blue
    
    # ===== PREMIUM TYPOGRAPHY STYLES =====
    
    # Main title - Ultra bold black
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=34,
        textColor=PURE_BLACK,
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName=font_bold,
        leading=40,
        textTransform='uppercase',
        wordWrap='LTR'
    )
    
    # Subtitle
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=13,
        textColor=LIGHT_SLATE,
        alignment=TA_CENTER,
        spaceAfter=24,
        fontName=font_family,
        letterSpacing=1.5
    )
    
    # Date style
    date_style = ParagraphStyle(
        'Date',
        parent=styles['Normal'],
        fontSize=10,
        textColor=SILVER,
        alignment=TA_CENTER,
        spaceAfter=36,
        fontName=font_italic,
        letterSpacing=0.8
    )
    
    # Section headers - Jet black background, white text
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=15,
        textColor=PURE_WHITE,
        spaceAfter=12,
        spaceBefore=30,
        fontName=font_bold,
        alignment=TA_LEFT,
        backColor=PURE_BLACK,
        borderPadding=12,
        leading=18,
        textTransform='uppercase',
        leftIndent=0,
        rightIndent=0,
        firstLineIndent=0
    )
    
    # Subsection headers - Bold black on light gray background
    subsection_style = ParagraphStyle(
        'SubsectionHeader',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=PURE_BLACK,
        spaceAfter=8,
        spaceBefore=18,
        fontName=font_bold,
        alignment=TA_LEFT,
        backColor=HexColor('#f5f5f5'),
        borderPadding=10,
        borderWidth=0.5,
        borderColor=PURE_BLACK,
        leading=14,
        textTransform='uppercase',
        leftIndent=8,
        rightIndent=8
    )
    
    # Article headlines - Ultra bold black with tracking
    headline_style = ParagraphStyle(
        'ArticleHeadline',
        parent=styles['Heading4'],
        fontSize=11,
        textColor=PURE_BLACK,  # Explicitly black
        spaceAfter=4,
        spaceBefore=12,
        fontName=font_bold,
        alignment=TA_LEFT,
        leftIndent=0,
        leading=14,
        wordWrap='LTR'
    )
    
    # Summary text - Dark slate, justified
    summary_style = ParagraphStyle(
        'ArticleSummary',
        parent=styles['Normal'],
        fontSize=9.5,
        textColor=DARK_SLATE,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
        fontName=font_family,
        leftIndent=4,
        rightIndent=4,
        leading=14,
        wordWrap='LTR'
    )
    
    # Source info - Light slate with blue hyperlink
    source_style = ParagraphStyle(
        'ArticleSource',
        parent=styles['Normal'],
        fontSize=8.5,
        textColor=LIGHT_SLATE,
        alignment=TA_LEFT,
        spaceAfter=16,
        fontName=font_family,
        leftIndent=4
    )
    
    # Link style specifically for hyperlinks
    link_style = ParagraphStyle(
        'ArticleLink',
        parent=source_style,
        textColor=HYPERLINK_BLUE,
        underline=True,
        backColor=None
    )
    
    # Stats box style
    stats_style = ParagraphStyle(
        'Stats',
        parent=styles['Normal'],
        fontSize=10.5,
        textColor=DARK_SLATE,
        spaceAfter=32,
        alignment=TA_CENTER,
        fontName=font_medium,
        leading=17
    )
    
    # Tag style for categories
    tag_style = ParagraphStyle(
        'Tag',
        parent=styles['Normal'],
        fontSize=7.5,
        textColor=PURE_WHITE,
        alignment=TA_CENTER,
        fontName=font_bold,
        backColor=PURE_BLACK,
        borderPadding=4,
        leading=9,
        leftIndent=4,
        rightIndent=4,
        spaceBefore=2,
        spaceAfter=2
    )
    
    # Footer style
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=SILVER,
        alignment=TA_CENTER,
        fontName=font_family,
        leading=10
    )
    
    # ===== CUSTOM HEADER AND FOOTER FUNCTION =====
    def header_footer_canvas(canvas_obj, doc):
        canvas_obj.saveState()
        
        page_width = doc.pagesize[0]
        page_height = doc.pagesize[1]
        
        # ===== HEADER SECTION =====
        # Header top line - thin black line
        canvas_obj.setStrokeColor(PURE_BLACK)
        canvas_obj.setLineWidth(0.5)
        header_y = page_height - 0.7*inch
        canvas_obj.line(0.6*inch, header_y, page_width - 0.6*inch, header_y)
        
        # Header text - "<b>CEO OFFICE - RESEARCH TEAM </b>" at top right
        canvas_obj.setFillColor(PURE_BLACK)
        canvas_obj.setFont(font_medium, 9)
        header_text = "CEO OFFICE - RESEARCH TEAM"
        
        # Position at top right (right-aligned)
        text_width = canvas_obj.stringWidth(header_text, font_medium, 9)
        header_x = page_width - 0.6*inch  # Right margin position
        
        # Draw header text at top right
        canvas_obj.drawRightString(header_x, header_y + 0.1*inch, header_text)
        
               
        # ===== FOOTER SECTION =====
        # Thin black line at bottom
        footer_y = 0.5*inch
        canvas_obj.setStrokeColor(PURE_BLACK)
        canvas_obj.setLineWidth(0.5)
        canvas_obj.line(0.6*inch, footer_y, page_width - 0.6*inch, footer_y)

        canvas_obj.setFillColor(SILVER)

        # MS HOLDINGS - Bold + Italic
        canvas_obj.setFont("Helvetica-BoldOblique", 8)
        left_text = "MS HOLDINGS"
        canvas_obj.drawString(0.6*inch, 0.3*inch, left_text)

        # CONFIDENTIAL - Regular or whatever font you want (example: regular)
        canvas_obj.setFont("Helvetica", 8)
        center_text = "CONFIDENTIAL"
        canvas_obj.drawCentredString(page_width/2, 0.3*inch, center_text)

        # PAGE number - Bold only
        canvas_obj.setFont("Helvetica-Bold", 8)
        right_text = f"PAGE {doc.page}"
        canvas_obj.drawRightString(page_width - 0.6*inch, 0.3*inch, right_text)

        canvas_obj.restoreState()
    
    # ===== TITLE PAGE =====
    # On title page, we'll use a special header without the line at the top
    def title_page_header_footer(canvas_obj, doc):
        canvas_obj.saveState()
        
        page_width = doc.pagesize[0]
        page_height = doc.pagesize[1]
        
        # ===== HEADER FOR TITLE PAGE ONLY =====
        # Header text - "CEO OFFICE - RESEARCH TEAM" at top right
        canvas_obj.setFillColor(PURE_BLACK)
        canvas_obj.setFont(font_medium, 9)
        header_text = "CEO OFFICE - RESEARCH TEAM"
        
        # Position at top right (right-aligned)
        text_width = canvas_obj.stringWidth(header_text, font_medium, 9)
        header_x = page_width - 0.6*inch  # Right margin position
        header_y = page_height - 0.5*inch
        
        # Draw header text at top right (without top line on title page)
        canvas_obj.drawRightString(header_x, header_y, header_text)
        
        # ===== FOOTER SECTION (same as others) =====
        # Thin black line at bottom
        footer_y = 0.5*inch
        canvas_obj.setStrokeColor(PURE_BLACK)
        canvas_obj.setLineWidth(0.5)
        canvas_obj.line(0.6*inch, footer_y, page_width - 0.6*inch, footer_y)
        
        # Footer text - minimalist
        canvas_obj.setFillColor(SILVER)
        canvas_obj.setFont(font_family, 8)
        
        left_text = "MS HOLDINGS"
        canvas_obj.drawString(0.6*inch, 0.3*inch, left_text)
        
        center_text = "CONFIDENTIAL"
        canvas_obj.drawCentredString(page_width/2, 0.3*inch, center_text)
        
        right_text = f"PAGE {doc.page}"
        canvas_obj.drawRightString(page_width - 0.6*inch, 0.3*inch, right_text)
        
        canvas_obj.restoreState()
    
    # Add title page content
    story.append(Spacer(1, 1.5*inch))  # Reduced space to account for header
    
    # Main title
    story.append(Paragraph("MS HOLDINGS<br/>MARKET BRIEF", title_style))
    story.append(Spacer(1, 0.08*inch))
    
    # Subtitle
    story.append(Paragraph("MARKET REPORT", subtitle_style))
    
    # Date
    current_date = datetime.now()
    story.append(Paragraph(
        f"{current_date.strftime('%B %d, %Y').upper()} • {current_date.strftime('%A').upper()}",
        date_style
    ))
    
    # Thin divider
    story.extend(create_minimalist_line(width=0.75, color=PURE_BLACK, 
                                        space_before=20, space_after=24))
    
    # Statistics - Premium layout
    total_articles = 0
    pillar_stats = []
    section_stats = []
    
    # Process each data section
    sections_order = [
        ('p1_entity', 'P1 Entity'),
        ('p1_market', 'P1 Market'),
        ('p2_entity', 'P2 Entity'),
        ('p2_market', 'P2 Market'),
        ('p3_tech', 'Tech Hiring'),
        ('p3_market', 'Tech Market'),
        ('e7_market', 'RE Market'),
        ('e7_developer', 'RE Developer')
    ]
    
    for key, label in sections_order:
        if key in all_data:
            if key.endswith('_entity'):
                count = sum(len(articles) for articles in all_data[key].values())
            else:
                count = len(all_data[key])
            total_articles += count
            if count > 0:
                pillar_stats.append(f"{label}: {count}")
    
    # Create stats paragraph
    stats_text = f"""
    <para align="center">
    <b>TOTAL ARTICLES: {total_articles}</b><br/>
    <font size="9" color="{LIGHT_SLATE.hexval()}">
    {chr(0x2022)} {chr(0x2022)} {chr(0x2022)}<br/><br/>
    {' &nbsp;&nbsp; '.join(pillar_stats)}<br/><br/>
    Generated {datetime.now().strftime('%H:%M')} IST
    </font>
    </para>
    """
    
    story.append(Paragraph(stats_text, stats_style))
    
    # Bottom thin divider
    story.extend(create_minimalist_line(width=0.75, color=PURE_BLACK, 
                                        space_before=24, space_after=30))
    
    # Confidential notice
    confidential = Paragraph(
        "<para align='center'><font size='8' color='#8a8a8a'>FOR INTERNAL USE ONLY</font></para>",
        stats_style
    )
    story.append(confidential)
    
    story.append(PageBreak())
    
    # Helper function to add articles with hyperlinks
    def add_articles_section(section_name, articles, category_label=""):
        """Add a section of articles with consistent styling and hyperlinks"""
        if not articles:
            return
        
        story.append(Paragraph(section_name, section_style))
        story.append(Spacer(1, 0.1*inch))
        
        for idx, article in enumerate(articles, 1):
            # Headline - always black
            headline = article.get("headline", "").strip()
            if headline:
                story.append(Paragraph(f"• {headline}", headline_style))
            
            # Summary
            summary = article.get("ai_summary", article.get("summary", ""))
            if summary:
                clean_summary = summary[:480] + "..." if len(summary) > 480 else summary
                story.append(Paragraph(clean_summary, summary_style))
            
            # Source and metadata with HYPERLINK
            source_text = article.get("source", "").upper()
            time_str = get_time_ago(article.get("published", ""))
            url = article.get("url", "")
            category_label = category_label
            
            # Create source info with blue hyperlink
            if url:
                # Get domain for display
                domain = get_domain_from_url(url)
                source_display = domain if domain else source_text
                
                # Create hyperlink
                hyperlink = create_hyperlink(url, source_display, HYPERLINK_BLUE)
                
                source_html = f"""
                <para>
                {hyperlink}
                <font color="{SILVER.hexval()}"> • {time_str}</font>
                <font color="{LIGHT_SLATE.hexval()}"> • {category_label}</font>
                </para>
                """
            else:
                # Fallback without hyperlink
                source_html = f"""
                <para>
                <font color="{PURE_BLACK.hexval()}"><b>{source_text}</b></font> 
                <font color="{SILVER.hexval()}"> • {time_str}</font>
                <font color="{LIGHT_SLATE.hexval()}"> • {category_label}</font>
                </para>
                """
            
            source_para = Paragraph(source_html, source_style)
            story.append(source_para)
            
            # Add subtle divider between articles (except last)
            if idx < len(articles):
                story.extend(create_minimalist_line(width=0.25, color=HexColor('#e0e0e0'), 
                                                   space_before=8, space_after=8))
    
    # ===== PILLAR 1: ENTITY INTELLIGENCE =====
    if 'p1_entity' in all_data and all_data['p1_entity']:
        story.append(Paragraph("PILLAR 1 — ENTITY INTELLIGENCE", section_style))
        
        for entity, articles in all_data['p1_entity'].items():
            if articles:
                story.append(Paragraph(f"{entity.upper()}", subsection_style))
                add_articles_section("", articles, "P1 ENTITY")
                story.append(Spacer(1, 0.2*inch))
        
        story.append(PageBreak())
    
    # ===== PILLAR 1: MARKET INTELLIGENCE =====
    if 'p1_market' in all_data and all_data['p1_market']:
        add_articles_section("PILLAR 1 — MARKET INTELLIGENCE", 
                           all_data['p1_market'][:15], "P1 MARKET")
        story.append(PageBreak())
    
    # ===== PILLAR 2: ENTITY INTELLIGENCE =====
    if 'p2_entity' in all_data and all_data['p2_entity']:
        story.append(Paragraph("PILLAR 2 — ENTITY INTELLIGENCE", section_style))
        
        for entity, articles in all_data['p2_entity'].items():
            if articles:
                story.append(Paragraph(f"{entity.upper()}", subsection_style))
                add_articles_section("", articles, "P2 ENTITY")
                story.append(Spacer(1, 0.2*inch))
        
        story.append(PageBreak())
    
    # ===== PILLAR 2: MARKET INTELLIGENCE =====
    if 'p2_market' in all_data and all_data['p2_market']:
        add_articles_section("PILLAR 2 — MARKET INTELLIGENCE", 
                           all_data['p2_market'][:15], "P2 MARKET")
        story.append(PageBreak())
    
    # ===== PILLAR 3: TECH HIRING INTELLIGENCE =====
    if 'p3_tech' in all_data and all_data['p3_tech']:
        story.append(Paragraph("TECH HIRING INTELLIGENCE", section_style))
        
        # Group by field
        articles_by_field = {}
        for article in all_data['p3_tech']:
            field = article.get('field', 'General Tech').upper()
            if field not in articles_by_field:
                articles_by_field[field] = []
            articles_by_field[field].append(article)
        
        for field, field_articles in articles_by_field.items():
            if field_articles:
                story.append(Paragraph(field, subsection_style))
                add_articles_section("", field_articles[:8], "TECH HIRING")
                story.append(Spacer(1, 0.2*inch))
        
        story.append(PageBreak())
    
    # ===== PILLAR 3: MARKET INTELLIGENCE =====
    if 'p3_market' in all_data and all_data['p3_market']:
        add_articles_section("TECH MARKET INTELLIGENCE", 
                           all_data['p3_market'][:10], "TECH MARKET")
        story.append(PageBreak())
    
    # ===== E7: REAL ESTATE INTELLIGENCE =====
    has_e7_market = 'e7_market' in all_data and all_data['e7_market']
    has_e7_developer = 'e7_developer' in all_data and all_data['e7_developer']
    
    if has_e7_market or has_e7_developer:
        story.append(Paragraph("REAL ESTATE INTELLIGENCE", section_style))
        story.append(Spacer(1, 0.15*inch))
        
        if has_e7_market:
            story.append(Paragraph("MARKET UPDATES", subsection_style))
            add_articles_section("", all_data['e7_market'][:10], "E7 MARKET")
            story.append(Spacer(1, 0.25*inch))
        
        if has_e7_developer:
            story.append(Paragraph("DEVELOPER UPDATES", subsection_style))
            add_articles_section("", all_data['e7_developer'][:10], "E7 DEVELOPER")
    
    # ===== FINAL PAGE =====
    story.append(PageBreak())
    story.append(Spacer(1, 2.2*inch))  # Adjusted for header
    
    # End of report
    end_title = Paragraph(
        "<para align='center'><font size='24' color='#000000'>END OF REPORT</font></para>",
        title_style
    )
    story.append(end_title)
    
    story.append(Spacer(1, 0.3*inch))
    
    # Final divider
    story.extend(create_minimalist_line(width=1, color=PURE_BLACK, 
                                       space_before=20, space_after=20))
    
    # Footer note
    footer_note = Paragraph(
        f"""
        <para align='center'>
        <font size='9' color='#666666'>
        Report generated on {current_date.strftime('%B %d, %Y')} at {current_date.strftime('%H:%M')}<br/>
        Total articles processed: <b>{total_articles}</b><br/><br/>
        This is an automated intelligence briefing.<br/>
        <i>For inquiries, contact <B>CEO Office - Research Team</b></i>
        </font>
        </para>
        """,
        stats_style
    )
    story.append(footer_note)
    
    # Build PDF with header and footer support
    try:
        doc.build(
            story, 
            onFirstPage=title_page_header_footer, 
            onLaterPages=header_footer_canvas
        )
        logger.info(f"✓ Premium Black Theme PDF created with hyperlinks and header: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"❌ PDF generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

# Additional utility function for better text handling
def truncate_text(text, max_length, suffix="..."):
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)].rsplit(' ', 1)[0] + suffix
