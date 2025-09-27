import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from configurations.config import config
from typing import Optional

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_host = config.SMTP_HOST
        self.smtp_port = config.SMTP_PORT
        self.smtp_username = config.SMTP_USERNAME
        self.smtp_password = config.SMTP_PASSWORD
        self.smtp_use_tls = config.SMTP_USE_TLS
        self.smtp_use_ssl = config.SMTP_USE_SSL
        self.email_from = config.EMAIL_FROM

    def send_email(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
        """
        Send email with HTML content
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            text_content: Plain text content (optional)
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_from
            msg['To'] = to_email
            msg['Subject'] = subject

            # Add text content if provided
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)

            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            # Connect to SMTP server
            if self.smtp_use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                if self.smtp_use_tls:
                    server.starttls()

            # Login and send email
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def send_status_update_email(self, to_email: str, emergency_type: str, emergency_id: str, status: str) -> bool:
        """
        Send email notification for status update
        
        Args:
            to_email: Recipient email address
            emergency_type: Type of emergency (medical, police, electricity, fire)
            emergency_id: Emergency case ID
            status: New status
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        subject = f"AidLinkAI - Your {emergency_type.title()} Emergency Case Status Update"
        
        # Create beautiful HTML template
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Emergency Status Update</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f4f4f4;
                }}
                .container {{
                    background-color: #ffffff;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                    font-weight: 300;
                }}
                .content {{
                    padding: 30px;
                }}
                .status-badge {{
                    display: inline-block;
                    padding: 8px 16px;
                    border-radius: 20px;
                    font-weight: bold;
                    text-transform: uppercase;
                    font-size: 12px;
                    letter-spacing: 1px;
                }}
                .status-in-progress {{
                    background-color: #e3f2fd;
                    color: #1976d2;
                    border: 2px solid #1976d2;
                }}
                .emergency-info {{
                    background-color: #f8f9fa;
                    border-left: 4px solid #667eea;
                    padding: 20px;
                    margin: 20px 0;
                    border-radius: 0 5px 5px 0;
                }}
                .footer {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    color: #666;
                    font-size: 14px;
                }}
                .logo {{
                    font-size: 24px;
                    font-weight: bold;
                    margin-bottom: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🚨 AidLinkAI</div>
                    <h1>Emergency Status Update</h1>
                </div>
                
                <div class="content">
                    <h2>Your Emergency Case Status Has Been Updated</h2>
                    
                    <p>We're writing to inform you that your emergency case has been updated by our emergency response team.</p>
                    
                    <div class="emergency-info">
                        <h3>📋 Case Details</h3>
                        <p><strong>Emergency Type:</strong> {emergency_type.title()}</p>
                        <p><strong>Case ID:</strong> {emergency_id}</p>
                        <p><strong>New Status:</strong> <span class="status-badge status-in-progress">{status.replace('_', ' ')}</span></p>
                    </div>
                    
                    <p><strong>What this means:</strong></p>
                    <ul>
                        <li>Your emergency case has been assigned to professional {emergency_type} authorities</li>
                        <li>Emergency responders are now actively working on your case</li>
                        <li>You will receive updates as the situation progresses</li>
                        <li>If you have any questions or concerns, please contact us immediately</li>
                    </ul>
                    
                    <p>We understand that emergency situations can be stressful, and we want to assure you that our team is working diligently to resolve your case as quickly and safely as possible.</p>
                    
                    <p><strong>Important:</strong> If this is a life-threatening emergency, please call emergency services immediately (911 or your local emergency number).</p>
                </div>
                
                <div class="footer">
                    <p>This is an automated message from AidLinkAI Emergency Response System.</p>
                    <p>© 2024 AidLinkAI. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        AidLinkAI - Emergency Status Update
        
        Your {emergency_type.title()} emergency case (ID: {emergency_id}) status has been updated to: {status.replace('_', ' ')}
        
        Your emergency case has been assigned to professional {emergency_type} authorities and emergency responders are now actively working on your case.
        
        If this is a life-threatening emergency, please call emergency services immediately (911 or your local emergency number).
        
        Best regards,
        AidLinkAI Emergency Response Team
        """
        
        return self.send_email(to_email, subject, html_content, text_content)

    def send_resolution_request_email(self, to_email: str, emergency_type: str, emergency_id: str, message: str = None) -> bool:
        """
        Send email notification for resolution request with approval buttons
        
        Args:
            to_email: Recipient email address
            emergency_type: Type of emergency (medical, police, electricity, fire)
            emergency_id: Emergency case ID
            message: Custom message from authority
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        subject = f"AidLinkAI - Resolution Request for Your {emergency_type.title()} Emergency Case"
        
        # Create beautiful HTML template with action buttons
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Resolution Request</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f4f4f4;
                }}
                .container {{
                    background-color: #ffffff;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                    font-weight: 300;
                }}
                .content {{
                    padding: 30px;
                }}
                .emergency-info {{
                    background-color: #f8f9fa;
                    border-left: 4px solid #28a745;
                    padding: 20px;
                    margin: 20px 0;
                    border-radius: 0 5px 5px 0;
                }}
                .action-buttons {{
                    text-align: center;
                    margin: 30px 0;
                }}
                .btn {{
                    display: inline-block;
                    padding: 15px 30px;
                    margin: 10px;
                    text-decoration: none;
                    border-radius: 25px;
                    font-weight: bold;
                    font-size: 16px;
                    transition: all 0.3s ease;
                    border: none;
                    cursor: pointer;
                }}
                .btn-resolved {{
                    background-color: #28a745;
                    color: white;
                }}
                .btn-resolved:hover {{
                    background-color: #218838;
                    transform: translateY(-2px);
                }}
                .btn-not-resolved {{
                    background-color: #dc3545;
                    color: white;
                }}
                .btn-not-resolved:hover {{
                    background-color: #c82333;
                    transform: translateY(-2px);
                }}
                .footer {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    color: #666;
                    font-size: 14px;
                }}
                .logo {{
                    font-size: 24px;
                    font-weight: bold;
                    margin-bottom: 10px;
                }}
                .message-box {{
                    background-color: #e9ecef;
                    border-radius: 8px;
                    padding: 15px;
                    margin: 20px 0;
                    border-left: 4px solid #6c757d;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">✅ AidLinkAI</div>
                    <h1>Resolution Request</h1>
                </div>
                
                <div class="content">
                    <h2>Your Emergency Case Resolution Request</h2>
                    
                    <p>Great news! The {emergency_type} authorities have completed their work on your emergency case and are requesting your confirmation to mark it as resolved.</p>
                    
                    <div class="emergency-info">
                        <h3>📋 Case Details</h3>
                        <p><strong>Emergency Type:</strong> {emergency_type.title()}</p>
                        <p><strong>Case ID:</strong> {emergency_id}</p>
                        <p><strong>Status:</strong> Awaiting Your Approval</p>
                    </div>
                    
                    {f'<div class="message-box"><h4>💬 Message from {emergency_type.title()} Authorities:</h4><p>"{message}"</p></div>' if message else ''}
                    
                    <p><strong>Please review your case and let us know:</strong></p>
                    
                    <div class="action-buttons">
                        <a href="mailto:{config.EMAIL_FROM}?subject=Case {emergency_id} - RESOLVED&body=Hello AidLinkAI Team,%0D%0A%0D%0AI confirm that my {emergency_type} emergency case (ID: {emergency_id}) has been RESOLVED to my satisfaction.%0D%0A%0D%0AThank you for your assistance.%0D%0A%0D%0ABest regards," class="btn btn-resolved">
                            ✅ Mark as Resolved
                        </a>
                        <a href="mailto:{config.EMAIL_FROM}?subject=Case {emergency_id} - NOT RESOLVED&body=Hello AidLinkAI Team,%0D%0A%0D%0AI need to report that my {emergency_type} emergency case (ID: {emergency_id}) has NOT been resolved to my satisfaction.%0D%0A%0D%0APlease provide additional assistance.%0D%0A%0D%0ABest regards," class="btn btn-not-resolved">
                            ❌ Not Resolved
                        </a>
                    </div>
                    
                    <p><strong>What happens next?</strong></p>
                    <ul>
                        <li><strong>If you click "Mark as Resolved":</strong> Your case will be closed and marked as successfully resolved</li>
                        <li><strong>If you click "Not Resolved":</strong> Our team will review your case and provide additional assistance</li>
                        <li>You can also reply to this email with any additional comments or concerns</li>
                    </ul>
                    
                    <p>Thank you for using AidLinkAI. We hope we were able to help you during this emergency situation.</p>
                </div>
                
                <div class="footer">
                    <p>This is an automated message from AidLinkAI Emergency Response System.</p>
                    <p>© 2024 AidLinkAI. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        AidLinkAI - Resolution Request
        
        The {emergency_type} authorities have completed their work on your emergency case (ID: {emergency_id}) and are requesting your confirmation to mark it as resolved.
        
        {f'Message from {emergency_type.title()} Authorities: "{message}"' if message else ''}
        
        Please reply to this email with one of the following:
        
        1. "RESOLVED" - if your case has been resolved to your satisfaction
        2. "NOT RESOLVED" - if you need additional assistance
        
        You can also reply with any additional comments or concerns.
        
        Thank you for using AidLinkAI.
        
        Best regards,
        AidLinkAI Emergency Response Team
        """
        
        return self.send_email(to_email, subject, html_content, text_content)

# Create global instance
email_service = EmailService()
