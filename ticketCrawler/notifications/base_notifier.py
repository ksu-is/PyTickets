# -*- coding: utf-8 -*-
"""Base notifier class."""
from abc import ABC, abstractmethod


class BaseNotifier(ABC):
    """Abstract base class for notification channels."""
    
    def __init__(self, config=None):
        """
        Initialize notifier.
        
        Args:
            config (dict): Notifier configuration
        """
        self.config = config or {}
    
    @abstractmethod
    def notify(self, message, **kwargs):
        """
        Send notification.
        
        Args:
            message (str): Notification message
            **kwargs: Additional parameters (subject, html, etc.)
            
        Returns:
            bool: True if notification sent successfully
        """
        pass
    
    @abstractmethod
    def __repr__(self):
        """Return string representation."""
        pass
