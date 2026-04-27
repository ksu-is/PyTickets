# -*- coding: utf-8 -*-
"""Factory for creating authenticators."""
from .authenticators.facebook import FacebookAuthenticator
from .authenticators.email_password import EmailPasswordAuthenticator
from .authenticators.oauth import OAuthAuthenticator


class AuthenticatorFactory:
    """Factory for creating authenticators based on auth type."""
    
    AUTHENTICATORS = {
        'facebook': FacebookAuthenticator,
        'email_password': EmailPasswordAuthenticator,
        'oauth': OAuthAuthenticator,
    }
    
    @classmethod
    def create_authenticator(cls, auth_type, config):
        """
        Create an authenticator instance.
        
        Args:
            auth_type (str): Type of authenticator ('facebook', 'email_password', 'oauth')
            config (dict): Authentication configuration
            
        Returns:
            BaseAuthenticator: Configured authenticator instance
            
        Raises:
            ValueError: If auth type not found
        """
        if auth_type not in cls.AUTHENTICATORS:
            available = ', '.join(cls.AUTHENTICATORS.keys())
            raise ValueError(f"Unknown auth type: {auth_type}. Available: {available}")
        
        auth_class = cls.AUTHENTICATORS[auth_type]
        return auth_class(config)
    
    @classmethod
    def register_authenticator(cls, auth_type, auth_class):
        """
        Register a new authenticator type.
        
        Args:
            auth_type (str): Type name
            auth_class: Authenticator class (must inherit from BaseAuthenticator)
        """
        cls.AUTHENTICATORS[auth_type] = auth_class
    
    @classmethod
    def list_authenticators(cls):
        """List all registered authenticator types."""
        return list(cls.AUTHENTICATORS.keys())
