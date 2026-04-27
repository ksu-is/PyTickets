# -*- coding: utf-8 -*-
"""Email notification channel."""
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..base_notifier import BaseNotifier


class EmailNotifier(BaseNotifier):
    """Send notifications via email."""
    
    def __init__(self, config):
        """
        Initialize email notifier.
        
        Args:
            config (dict): Email configuration with provider-specific settings
        """
        super().__init__(config)
        self.provider = config.get('provider', 'mailgun')
        self.sender = config.get('sender')
        self.recipient = config.get('recipient') or config.get('to')
        
        if not self.sender or not self.recipient:
            raise ValueError("Email notifier requires 'sender' and 'recipient' in config")
        
        # Validate provider-specific config
        if self.provider == 'mailgun':
            self.mailgun_key = config.get('mailgun_key')
            self.mailgun_domain = config.get('mailgun_domain')
            if not self.mailgun_key or not self.mailgun_domain:
                raise ValueError("Mailgun notifier requires 'mailgun_key' and 'mailgun_domain'")
        
        elif self.provider == 'smtp':
            self.smtp_host = config.get('smtp_host')
            self.smtp_port = config.get('smtp_port', 587)
            self.smtp_user = config.get('smtp_user')
            self.smtp_password = config.get('smtp_password')
            if not self.smtp_host or not self.smtp_user or not self.smtp_password:
                raise ValueError("SMTP notifier requires 'smtp_host', 'smtp_user', 'smtp_password'")
    
    def notify(self, message, **kwargs):
        """
        Send email notification.
        
        Args:
            message (str): Email body
            **kwargs: subject, html, attachments, etc.
            
        Returns:
            bool: True if sent successfully
        """
        subject = kwargs.get('subject', 'Ticket Notification')
        
        if self.provider == 'mailgun':
            return self._send_via_mailgun(message, subject, **kwargs)
        elif self.provider == 'smtp':
            return self._send_via_smtp(message, subject, **kwargs)
        
        return False
    
    def _send_via_mailgun(self, message, subject, **kwargs):
        """Send via Mailgun API."""
        try:
            url = f"https://api.mailgun.net/v3/{self.mailgun_domain}/messages"
            
            data = {
                "from": self.sender,
                "to": self.recipient,
                "subject": subject,
                "text": message
            }
            
            # Add HTML version if provided
            if 'html' in kwargs:
                data['html'] = kwargs['html']
            
            response = requests.post(
                url,
                auth=("api", self.mailgun_key),
                data=data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                return True
            else:
                print(f"Mailgun error: {response.status_code} - {response.text}")
                return False
        
        except Exception as e:
            print(f"Mailgun notification failed: {str(e)}")
            return False
    
    def _send_via_smtp(self, message, subject, **kwargs):
        """Send via SMTP (Gmail, Outlook, etc.)."""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender
            msg['To'] = self.recipient
            
            # Add text part
            msg.attach(MIMEText(message, 'plain'))
            
            # Add HTML part if provided
            if 'html' in kwargs:
                msg.attach(MIMEText(kwargs['html'], 'html'))
            
            # Connect and send
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.sender, self.recipient, msg.as_string())
            
            return True
        
        except Exception as e:
            print(f"SMTP notification failed: {str(e)}")
            return False
    
    def notify_ticket_found(self, ticket_data, **kwargs):
        """
        Send nicely formatted ticket notification.
        
        Args:
            ticket_data (dict): Ticket information
            
        Returns:
            bool: True if sent successfully
        """
        subject = kwargs.get('subject', 'Ticket Found!')
        
        # Build HTML message
        html = f"""
        <html>
            <body>
                <h2>Ticket Found!</h2>
                <table border="1" cellpadding="10">
                    <tr><td>Price:</td><td>{ticket_data.get('price', 'N/A')}</td></tr>
                    <tr><td>Seat Type:</td><td>{ticket_data.get('seat_type', 'N/A')}</td></tr>
                    <tr><td>Date:</td><td>{ticket_data.get('date', 'N/A')}</td></tr>
                    <tr><td>Quantity:</td><td>{ticket_data.get('quantity', 'N/A')}</td></tr>
                    <tr><td>URL:</td><td><a href="{ticket_data.get('url', '#')}">View Ticket</a></td></tr>
                </table>
                <p><a href="{ticket_data.get('url', '#')}">Reserve Now</a></p>
            </body>
        </html>
        """
        
        message = f"""
        Ticket Found!
        
        Price: {ticket_data.get('price', 'N/A')}
        Seat Type: {ticket_data.get('seat_type', 'N/A')}
        Date: {ticket_data.get('date', 'N/A')}
        Quantity: {ticket_data.get('quantity', 'N/A')}
        
        Link: {ticket_data.get('url', 'N/A')}
        """
        
        return self.notify(message, subject=subject, html=html)
    
    def __repr__(self):
        """Return string representation."""
        return f"EmailNotifier({self.provider}, to={self.recipient})"
