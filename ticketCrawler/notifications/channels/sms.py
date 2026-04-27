# -*- coding: utf-8 -*-
"""SMS notification channel."""
import requests
from ..base_notifier import BaseNotifier


class SMSNotifier(BaseNotifier):
    """Send notifications via SMS."""
    
    def __init__(self, config):
        """
        Initialize SMS notifier.
        
        Args:
            config (dict): SMS configuration with provider settings
        """
        super().__init__(config)
        self.provider = config.get('provider', 'twilio')
        self.phone_number = config.get('phone_number')
        
        if not self.phone_number:
            raise ValueError("SMS notifier requires 'phone_number' in config")
        
        if self.provider == 'twilio':
            self.account_sid = config.get('account_sid')
            self.auth_token = config.get('auth_token')
            self.from_number = config.get('from_number')
            if not all([self.account_sid, self.auth_token, self.from_number]):
                raise ValueError("Twilio notifier requires 'account_sid', 'auth_token', 'from_number'")
    
    def notify(self, message, **kwargs):
        """
        Send SMS notification.
        
        Args:
            message (str): SMS message
            **kwargs: Additional parameters
            
        Returns:
            bool: True if sent successfully
        """
        if self.provider == 'twilio':
            return self._send_via_twilio(message)
        
        return False
    
    def _send_via_twilio(self, message):
        """Send via Twilio API."""
        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
            
            data = {
                'From': self.from_number,
                'To': self.phone_number,
                'Body': message
            }
            
            response = requests.post(
                url,
                data=data,
                auth=(self.account_sid, self.auth_token),
                timeout=10
            )
            
            if response.status_code == 201:
                return True
            else:
                print(f"Twilio error: {response.status_code} - {response.text}")
                return False
        
        except Exception as e:
            print(f"Twilio notification failed: {str(e)}")
            return False
    
    def __repr__(self):
        """Return string representation."""
        masked_number = self.phone_number[-4:].rjust(len(self.phone_number), '*')
        return f"SMSNotifier(to={masked_number})"
