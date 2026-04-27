# -*- coding: utf-8 -*-
"""Telegram notification channel."""
import requests
from ..base_notifier import BaseNotifier


class TelegramNotifier(BaseNotifier):
    """Send notifications via Telegram."""
    
    def __init__(self, config):
        """
        Initialize Telegram notifier.
        
        Args:
            config (dict): Must contain 'token' and 'chat_id'
        """
        super().__init__(config)
        self.token = config.get('token')
        self.chat_id = config.get('chat_id')
        
        if not self.token or not self.chat_id:
            raise ValueError("Telegram notifier requires 'token' and 'chat_id' in config")
        
        self.base_url = f"https://api.telegram.org/bot{self.token}/"
    
    def notify(self, message, **kwargs):
        """
        Send Telegram message.
        
        Args:
            message (str): Message text
            **kwargs: Optional parameters (parse_mode, disable_web_page_preview, etc.)
            
        Returns:
            bool: True if sent successfully
        """
        try:
            url = self.base_url + "sendMessage"
            params = {
                'text': message,
                'chat_id': self.chat_id,
                'parse_mode': kwargs.get('parse_mode', 'HTML'),
                'disable_web_page_preview': kwargs.get('disable_web_page_preview', True)
            }
            
            response = requests.post(url, data=params, timeout=10)
            
            if response.status_code == 200:
                return True
            else:
                print(f"Telegram error: {response.status_code} - {response.text}")
                return False
        
        except Exception as e:
            print(f"Telegram notification failed: {str(e)}")
            return False
    
    def notify_html(self, message, **kwargs):
        """
        Send HTML-formatted Telegram message.
        
        Args:
            message (str): HTML message text
            
        Returns:
            bool: True if sent successfully
        """
        kwargs['parse_mode'] = 'HTML'
        return self.notify(message, **kwargs)
    
    def notify_markdown(self, message, **kwargs):
        """
        Send Markdown-formatted Telegram message.
        
        Args:
            message (str): Markdown message text
            
        Returns:
            bool: True if sent successfully
        """
        kwargs['parse_mode'] = 'Markdown'
        return self.notify(message, **kwargs)
    
    def __repr__(self):
        """Return string representation."""
        return f"TelegramNotifier(chat_id={self.chat_id})"
