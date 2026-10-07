# email_sender.py - Email sending functions
import os
import smtplib
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from config import SENDER_EMAIL, SENDER_PASSWORD, RECIPIENT_EMAIL

logger = logging.getLogger(__name__)

def send_unified_email_with_e7(pdf_path, stats):
    """Send email with unified PDF including E7 stats in black theme format"""
    try:
        # Validate PDF path
        if not pdf_path or not os.path.exists(pdf_path):
            logger.error(f"PDF file not found: {pdf_path}")
            return False
            
        pdf_size = os.path.getsize(pdf_path)
        if pdf_size == 0:
            logger.error(f"PDF file is empty: {pdf_path}")
            return False
            
        logger.info(f"Attaching PDF: {pdf_path} ({pdf_size} bytes)")
        
        # Create email message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"MS HOLDINGS - MARKET BRIEF • {datetime.now().strftime('%d %B %Y')}"
        msg['From'] = SENDER_EMAIL
        msg['To'] = ", ".join(RECIPIENT_EMAIL)
        
        # Create HTML email content with black theme
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 0; background-color: #000000; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
            
            <!-- Main Container -->
            <table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#000000">
                <tr>
                    <td align="center" style="padding: 40px 20px;">
                        
                        <!-- Content Box -->
                        <table width="600" cellpadding="0" cellspacing="0" border="0" bgcolor="#ffffff" style="border: 1px solid #000000; border-collapse: collapse;">
                            
                            <!-- Header Section -->
                            <tr>
                                <td style="background-color: #000000; padding: 30px 40px; text-align: center; border-bottom: 1px solid #4a4a4a;">
                                    <h1 style="color: #ffffff; font-size: 28px; font-weight: 700; letter-spacing: 2px; margin: 0 0 10px 0; text-transform: uppercase;">
                                        MS HOLDINGS - MARKET BRIEF
                                    </h1>
                                    <p style="color: #8a8a8a; font-size: 13px; letter-spacing: 1.5px; margin: 0; text-transform: uppercase;">
                                        Market Intelligence Report
                                    </p>
                                </td>
                            </tr>
                            
                            <!-- Date Section -->
                            <tr>
                                <td style="padding: 25px 40px; text-align: center; border-bottom: 1px solid #e0e0e0;">
                                    <p style="color: #666666; font-size: 11px; letter-spacing: 0.8px; margin: 0; text-transform: uppercase;">
                                        {datetime.now().strftime('%B %d, %Y').upper()} • {datetime.now().strftime('%A').upper()}
                                    </p>
                                    <div style="margin: 15px auto; width: 80px; height: 1px; background-color: #000000;"></div>
                                </td>
                            </tr>
                            
                            <!-- Executive Summary -->
                            <tr>
                                <td style="padding: 30px 40px; border-bottom: 1px solid #e0e0e0;">
                                    <h2 style="color: #000000; font-size: 16px; font-weight: 700; margin: 0 0 20px 0; text-transform: uppercase; letter-spacing: 1px;">
                                        EXECUTIVE SUMMARY
                                    </h2>
                                    
                                    <!-- Main Stats -->
                                    <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                        <tr>
                                            <td align="center" style="padding-bottom: 25px;">
                                                <div style="display: inline-block; background-color: #000000; padding: 12px 24px; border-radius: 2px;">
                                                    <p style="color: #ffffff; font-size: 18px; font-weight: 700; margin: 0; letter-spacing: 1px;">
                                                        TOTAL ARTICLES: {stats.get('total', 0)}
                                                    </p>
                                                </div>
                                            </td>
                                        </tr>
                                    </table>
                                    
                                    <!-- Stats Grid -->
                                    <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                        <tr>
                                            <!-- Column 1 -->
                                            <td width="50%" valign="top" style="padding-right: 15px;">
                                                <div style="margin-bottom: 20px;">
                                                    <h3 style="color: #000000; font-size: 11px; font-weight: 700; margin: 0 0 8px 0; text-transform: uppercase; letter-spacing: 1px;">
                                                        PILLAR 1
                                                    </h3>
                                                    <p style="color: #4a4a4a; font-size: 12px; margin: 0 0 5px 0;">
                                                        <span style="display: inline-block; width: 120px;">Entity:</span>
                                                        <span style="font-weight: 700;">{stats.get('p1_entity', 0)}</span>
                                                    </p>
                                                    <p style="color: #4a4a4a; font-size: 12px; margin: 0;">
                                                        <span style="display: inline-block; width: 120px;">Market:</span>
                                                        <span style="font-weight: 700;">{stats.get('p1_market', 0)}</span>
                                                    </p>
                                                </div>
                                                
                                                <div style="margin-bottom: 20px;">
                                                    <h3 style="color: #000000; font-size: 11px; font-weight: 700; margin: 0 0 8px 0; text-transform: uppercase; letter-spacing: 1px;">
                                                        PILLAR 3
                                                    </h3>
                                                    <p style="color: #4a4a4a; font-size: 12px; margin: 0 0 5px 0;">
                                                        <span style="display: inline-block; width: 120px;">Tech Hiring:</span>
                                                        <span style="font-weight: 700;">{stats.get('p3_tech', 0)}</span>
                                                    </p>
                                                    <p style="color: #4a4a4a; font-size: 12px; margin: 0;">
                                                        <span style="display: inline-block; width: 120px;">Market:</span>
                                                        <span style="font-weight: 700;">{stats.get('p3_market', 0)}</span>
                                                    </p>
                                                </div>
                                            </td>
                                            
                                            <!-- Column 2 -->
                                            <td width="50%" valign="top" style="padding-left: 15px;">
                                                <div style="margin-bottom: 20px;">
                                                    <h3 style="color: #000000; font-size: 11px; font-weight: 700; margin: 0 0 8px 0; text-transform: uppercase; letter-spacing: 1px;">
                                                        PILLAR 2
                                                    </h3>
                                                    <p style="color: #4a4a4a; font-size: 12px; margin: 0 0 5px 0;">
                                                        <span style="display: inline-block; width: 120px;">Entity:</span>
                                                        <span style="font-weight: 700;">{stats.get('p2_entity', 0)}</span>
                                                    </p>
                                                    <p style="color: #4a4a4a; font-size: 12px; margin: 0;">
                                                        <span style="display: inline-block; width: 120px;">Market:</span>
                                                        <span style="font-weight: 700;">{stats.get('p2_market', 0)}</span>
                                                    </p>
                                                </div>
                                                
                                                <div style="margin-bottom: 20px;">
                                                    <h3 style="color: #000000; font-size: 11px; font-weight: 700; margin: 0 0 8px 0; text-transform: uppercase; letter-spacing: 1px;">
                                                        REAL ESTATE
                                                    </h3>
                                                    <p style="color: #4a4a4a; font-size: 12px; margin: 0 0 5px 0;">
                                                        <span style="display: inline-block; width: 120px;">Market:</span>
                                                        <span style="font-weight: 700;">{stats.get('e7_market', 0)}</span>
                                                    </p>
                                                    <p style="color: #4a4a4a; font-size: 12px; margin: 0;">
                                                        <span style="display: inline-block; width: 120px;">Developer:</span>
                                                        <span style="font-weight: 700;">{stats.get('e7_developer', 0)}</span>
                                                    </p>
                                                </div>
                                            </td>
                                        </tr>
                                    </table>
                                    
                                    <!-- Divider -->
                                    <div style="margin: 25px 0; text-align: center;">
                                        <div style="display: inline-block; margin: 0 5px; width: 8px; height: 8px; background-color: #000000; border-radius: 50%;"></div>
                                        <div style="display: inline-block; margin: 0 5px; width: 8px; height: 8px; background-color: #000000; border-radius: 50%;"></div>
                                        <div style="display: inline-block; margin: 0 5px; width: 8px; height: 8px; background-color: #000000; border-radius: 50%;"></div>
                                    </div>
                                    
                                    <!-- Generation Info -->
                                    <p style="color: #666666; font-size: 10px; text-align: center; margin: 0; letter-spacing: 0.5px;">
                                        Generated {datetime.now().strftime('%H:%M')} IST • Automated Intelligence System
                                    </p>
                                </td>
                            </tr>
                            
                            <!-- Report Contents -->
                            <tr>
                                <td style="padding: 30px 40px; border-bottom: 1px solid #e0e0e0;">
                                    <h2 style="color: #000000; font-size: 16px; font-weight: 700; margin: 0 0 20px 0; text-transform: uppercase; letter-spacing: 1px;">
                                        REPORT CONTENTS
                                    </h2>
                                    
                                    <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                        <tr>
                                            <td style="padding-bottom: 15px;">
                                                <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                                    <tr>
                                                        <td width="30" valign="top" style="padding-right: 10px;">
                                                            <div style="width: 20px; height: 20px; background-color: #000000; display: flex; align-items: center; justify-content: center;">
                                                                <span style="color: #ffffff; font-size: 12px; font-weight: 700;">1</span>
                                                            </div>
                                                        </td>
                                                        <td valign="top">
                                                            <p style="color: #000000; font-size: 12px; font-weight: 700; margin: 0 0 3px 0;">
                                                                PILLAR 1 — WEALTH INTELLIGENCE
                                                            </p>
                                                            <p style="color: #666666; font-size: 11px; margin: 0;">
                                                                Entity & Market Analysis
                                                            </p>
                                                        </td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                        
                                        <tr>
                                            <td style="padding-bottom: 15px;">
                                                <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                                    <tr>
                                                        <td width="30" valign="top" style="padding-right: 10px;">
                                                            <div style="width: 20px; height: 20px; background-color: #000000; display: flex; align-items: center; justify-content: center;">
                                                                <span style="color: #ffffff; font-size: 12px; font-weight: 700;">2</span>
                                                            </div>
                                                        </td>
                                                        <td valign="top">
                                                            <p style="color: #000000; font-size: 12px; font-weight: 700; margin: 0 0 3px 0;">
                                                                PILLAR 2 — WEALTH INTELLIGENCE
                                                            </p>
                                                            <p style="color: #666666; font-size: 11px; margin: 0;">
                                                                Alternative Portfolio Analysis
                                                            </p>
                                                        </td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                        
                                        <tr>
                                            <td style="padding-bottom: 15px;">
                                                <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                                    <tr>
                                                        <td width="30" valign="top" style="padding-right: 10px;">
                                                            <div style="width: 20px; height: 20px; background-color: #000000; display: flex; align-items: center; justify-content: center;">
                                                                <span style="color: #ffffff; font-size: 12px; font-weight: 700;">3</span>
                                                            </div>
                                                        </td>
                                                        <td valign="top">
                                                            <p style="color: #000000; font-size: 12px; font-weight: 700; margin: 0 0 3px 0;">
                                                                TECH HIRING INTELLIGENCE
                                                            </p>
                                                            <p style="color: #666666; font-size: 11px; margin: 0;">
                                                                Recruitment & Market Trends
                                                            </p>
                                                        </td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                        
                                        <tr>
                                            <td>
                                                <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                                    <tr>
                                                        <td width="30" valign="top" style="padding-right: 10px;">
                                                            <div style="width: 20px; height: 20px; background-color: #000000; display: flex; align-items: center; justify-content: center;">
                                                                <span style="color: #ffffff; font-size: 12px; font-weight: 700;">4</span>
                                                            </div>
                                                        </td>
                                                        <td valign="top">
                                                            <p style="color: #000000; font-size: 12px; font-weight: 700; margin: 0 0 3px 0;">
                                                                REAL ESTATE INTELLIGENCE
                                                            </p>
                                                            <p style="color: #666666; font-size: 11px; margin: 0;">
                                                                Market & Developer Updates
                                                            </p>
                                                        </td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                    </table>
                                    
                                    <!-- Note -->
                                    <div style="margin-top: 25px; padding: 15px; background-color: #f5f5f5; border-left: 3px solid #000000;">
                                        <p style="color: #666666; font-size: 10px; font-style: italic; margin: 0; line-height: 1.4;">
                                            <strong>Note:</strong> All articles have been de-duplicated and organized with clickable source links in the attached PDF.
                                        </p>
                                    </div>
                                </td>
                            </tr>
                            
                            <!-- Footer -->
                            <tr>
                                <td style="background-color: #000000; padding: 25px 40px; text-align: center;">
                                    <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                        <tr>
                                            <td style="padding-bottom: 15px;">
                                                <p style="color: #ffffff; font-size: 10px; font-weight: 700; letter-spacing: 1px; margin: 0; text-transform: uppercase;">
                                                    CEO OFFICE • RESEARCH TEAM
                                                </p>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td>
                                                <p style="color: #8a8a8a; font-size: 9px; margin: 0 0 5px 0;">
                                                    MS HOLDINGS • INTELLIGENCE BRIEFING
                                                </p>
                                                <p style="color: #666666; font-size: 8px; margin: 0; letter-spacing: 0.5px;">
                                                    This is an automated intelligence report. For inquiries, contact Research Team - CEO Office
                                                </p>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            
                        </table>
                        
                        <!-- Bottom Note -->
                        <table width="600" cellpadding="0" cellspacing="0" border="0" style="margin-top: 20px;">
                            <tr>
                                <td align="center">
                                    <p style="color: #666666; font-size: 9px; margin: 0; letter-spacing: 0.5px;">
                                        CONFIDENTIAL • FOR INTERNAL USE ONLY
                                    </p>
                                </td>
                            </tr>
                        </table>
                        
                    </td>
                </tr>
            </table>
            
        </body>
        </html>
        """
        
        # Create plain text version
        text_content = f"""
INTELLIGENCE BRIEF
{datetime.now().strftime('%B %d, %Y')}

EXECUTIVE SUMMARY
────────────────
Total Articles: {stats.get('total', 0)}

PILLAR 1
  Entity: {stats.get('p1_entity', 0)}
  Market: {stats.get('p1_market', 0)}

PILLAR 2
  Entity: {stats.get('p2_entity', 0)}
  Market: {stats.get('p2_market', 0)}

TECH INTELLIGENCE
  Tech Hiring: {stats.get('p3_tech', 0)}
  Tech Market: {stats.get('p3_market', 0)}

REAL ESTATE INTELLIGENCE
  Market: {stats.get('e7_market', 0)}
  Developer: {stats.get('e7_developer', 0)}

REPORT CONTENTS
1. Pillar 1 — Market Intelligence
2. Pillar 2 — Market Intelligence
3. Tech Hiring Intelligence
4. Real Estate Intelligence

Generated: {datetime.now().strftime('%H:%M IST')}
Attached: {os.path.basename(pdf_path)}

────────────────
CEO OFFICE • RESEARCH TEAM
MS HOLDINGS • CONFIDENTIAL
For inquiries contact Research Team - CEO Office
────────────────
"""
        
        # Attach both HTML and plain text versions
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Attach the PDF file
        try:
            with open(pdf_path, "rb") as f:
                pdf_attachment = MIMEApplication(f.read(), _subtype="pdf")
                pdf_filename = f"Intelligence_Brief_{datetime.now().strftime('%Y%m%d')}.pdf"
                pdf_attachment.add_header('Content-Disposition', 'attachment', 
                                         filename=pdf_filename)
                msg.attach(pdf_attachment)
            logger.info("PDF attached successfully")
        except Exception as e:
            logger.error(f"Failed to attach PDF: {e}")
            return False
        
        # Send email
        try:
            logger.info("Connecting to SMTP server...")
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                logger.info("Logging in to email...")
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                logger.info("Sending email...")
                server.send_message(msg)
            
            logger.info(f"✅ Black theme email sent to {RECIPIENT_EMAIL}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ Email authentication failed: {e}")
            logger.error("Please check your email credentials and ensure 'Less Secure Apps' is enabled")
            return False
        except Exception as e:
            logger.error(f"❌ Email sending failed: {e}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Email sending failed: {e}")
        return False