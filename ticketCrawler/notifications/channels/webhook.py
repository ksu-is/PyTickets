# -*- coding: utf-8 -*-
"""Webhook notification channel."""
import json
import requests
from ..base_notifier import BaseNotifier


class WebhookNotifier(BaseNotifier):
    """Send notifications via HTTP webhook."""
    
    def __init__(self, config):
        """
        Initialize webhook notifier.
        
        Args:
            config (dict): Webhook configuration
        """
        super().__init__(config)
        self.webhook_url = config.get('url') or config.get('webhook_url')
        self.method = config.get('method', 'POST').upper()
        self.headers = config.get('headers', {})
        self.auth = config.get('auth')
        self.timeout = config.get('timeout', 30)
        
        if not self.webhook_url:
            raise ValueError("Webhook notifier requires 'url' in config")
    
    def notify(self, message, **kwargs):
        """
        Send webhook notification.
        
        Args:
            message (str): Notification message
            **kwargs: Additional data to send
            
        Returns:
            bool: True if sent successfully
        """
        try:
            # Build payload
            payload = {
                'message': message,
                'type': kwargs.get('type', 'ticket_notification'),
                **kwargs
            }
            
            # Set content type if not specified
            headers = self.headers.copy()
            if 'Content-Type' not in headers:
                headers['Content-Type'] = 'application/json'
            
            # Prepare auth if specified
            auth = None
            if self.auth:
                auth = (self.auth.get('username'), self.auth.get('password'))
            
            # Send webhook
            if self.method == 'POST':
                response = requests.post(
                    self.webhook_url,
                    json=payload,
                    headers=headers,
                    auth=auth,
                    timeout=self.timeout
                )
            elif self.method == 'PUT':
                response = requests.put(
                    self.webhook_url,
                    json=payload,
                    headers=headers,
                    auth=auth,
                    timeout=self.timeout
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {self.method}")
            
            if response.status_code in [200, 201, 202, 204]:
                return True
            else:
                print(f"Webhook error: {response.status_code} - {response.text}")
                return False
        
        except Exception as e:
            print(f"Webhook notification failed: {str(e)}")
            return False
    
    def notify_ticket(self, ticket_data, **kwargs):
        """
        Send structured ticket notification via webhook.
        
        Args:
            ticket_data (dict): Ticket information
            
        Returns:
            bool: True if sent successfully
        """
        return self.notify(
            message=f"Ticket found: {ticket_data.get('url', 'Unknown')}",
            ticket=ticket_data,
            type='ticket_found',
            **kwargs
        )
    
    def __repr__(self):
        """Return string representation."""
        return f"WebhookNotifier({self.method} {self.webhook_url})"
