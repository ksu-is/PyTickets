# -*- coding: utf-8 -*-
"""Notification manager."""
from .channels.telegram import TelegramNotifier
from .channels.email import EmailNotifier
from .channels.sms import SMSNotifier
from .channels.webhook import WebhookNotifier


class NotificationFactory:
    """Factory for creating notifiers."""
    
    NOTIFIERS = {
        'telegram': TelegramNotifier,
        'email': EmailNotifier,
        'sms': SMSNotifier,
        'webhook': WebhookNotifier,
    }
    
    @classmethod
    def create_notifier(cls, notifier_type, config):
        """
        Create a notifier instance.
        
        Args:
            notifier_type (str): Type of notifier
            config (dict): Notifier configuration
            
        Returns:
            BaseNotifier: Configured notifier instance
            
        Raises:
            ValueError: If notifier type not found
        """
        if notifier_type not in cls.NOTIFIERS:
            available = ', '.join(cls.NOTIFIERS.keys())
            raise ValueError(f"Unknown notifier type: {notifier_type}. Available: {available}")
        
        notifier_class = cls.NOTIFIERS[notifier_type]
        return notifier_class(config)
    
    @classmethod
    def register_notifier(cls, notifier_type, notifier_class):
        """Register a new notifier type."""
        cls.NOTIFIERS[notifier_type] = notifier_class
    
    @classmethod
    def list_notifiers(cls):
        """List all registered notifier types."""
        return list(cls.NOTIFIERS.keys())


class NotificationManager:
    """Manages multiple notification channels."""
    
    def __init__(self):
        """Initialize notification manager."""
        self.notifiers = []
    
    def add_notifier(self, notifier):
        """
        Add a notifier to the manager.
        
        Args:
            notifier: BaseNotifier instance
        """
        self.notifiers.append(notifier)
    
    def add_notifier_config(self, notifier_type, config):
        """
        Create and add a notifier from config.
        
        Args:
            notifier_type (str): Type of notifier
            config (dict): Notifier configuration
        """
        notifier = NotificationFactory.create_notifier(notifier_type, config)
        self.add_notifier(notifier)
    
    def remove_notifier(self, notifier):
        """Remove a notifier from the manager."""
        if notifier in self.notifiers:
            self.notifiers.remove(notifier)
    
    def notify(self, message, **kwargs):
        """
        Send notification through all configured channels.
        
        Args:
            message (str): Notification message
            **kwargs: Additional parameters
            
        Returns:
            dict: Results from each notifier {notifier: success}
        """
        results = {}
        
        for notifier in self.notifiers:
            try:
                success = notifier.notify(message, **kwargs)
                results[str(notifier)] = success
            except Exception as e:
                print(f"Error sending through {notifier}: {str(e)}")
                results[str(notifier)] = False
        
        return results
    
    def notify_ticket_found(self, ticket_data, **kwargs):
        """
        Send ticket found notification through all channels.
        
        Args:
            ticket_data (dict): Ticket information
            
        Returns:
            dict: Results from each notifier
        """
        results = {}
        
        for notifier in self.notifiers:
            try:
                # Check if notifier has specialized ticket method
                if hasattr(notifier, 'notify_ticket_found'):
                    success = notifier.notify_ticket_found(ticket_data, **kwargs)
                elif hasattr(notifier, 'notify_ticket'):
                    success = notifier.notify_ticket(ticket_data, **kwargs)
                else:
                    # Generic notification
                    message = f"Ticket found: {ticket_data.get('url', 'Unknown')}"
                    success = notifier.notify(message, **kwargs)
                
                results[str(notifier)] = success
            except Exception as e:
                print(f"Error sending through {notifier}: {str(e)}")
                results[str(notifier)] = False
        
        return results
    
    def __repr__(self):
        """Return string representation."""
        notifiers_str = ', '.join([repr(n) for n in self.notifiers])
        return f"NotificationManager({notifiers_str})"
