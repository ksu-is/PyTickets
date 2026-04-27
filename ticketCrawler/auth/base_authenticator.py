# -*- coding: utf-8 -*-
"""Base authenticator class."""
from abc import ABC, abstractmethod


class BaseAuthenticator(ABC):
    """Abstract base class for authentication methods."""
    
    def __init__(self, config):
        """
        Initialize authenticator with credentials config.
        
        Args:
            config (dict): Auth configuration including credentials
        """
        self.config = config
        self.credentials = config.get('credentials', {})
    
    @abstractmethod
    def authenticate(self, browser):
        """
        Perform authentication with the website.
        
        Args:
            browser: Selenium WebDriver instance
            
        Raises:
            Exception: If authentication fails
        """
        pass
    
    @abstractmethod
    def is_authenticated(self, browser):
        """
        Check if browser session is authenticated.
        
        Args:
            browser: Selenium WebDriver instance
            
        Returns:
            bool: True if authenticated, False otherwise
        """
        pass
