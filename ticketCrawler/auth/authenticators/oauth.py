# -*- coding: utf-8 -*-
"""OAuth authenticator for third-party providers."""
from .base_authenticator import BaseAuthenticator


class OAuthAuthenticator(BaseAuthenticator):
    """Generic OAuth authenticator for Google, Apple, etc."""
    
    def __init__(self, config):
        """Initialize OAuth authenticator."""
        super().__init__(config)
        self.provider = self.credentials.get('provider', 'google')
        self.email = self.credentials.get('email')
        self.password = self.credentials.get('password')
        self.login_button_text = self.credentials.get('login_button_text', f'Login with {self.provider.capitalize()}')
    
    def authenticate(self, browser):
        """
        Authenticate using OAuth provider (Google, Apple, etc.).
        
        Args:
            browser: Selenium WebDriver instance
            
        Raises:
            Exception: If authentication fails
        """
        if not self.email or not self.password:
            raise ValueError(f"Email and password required for {self.provider} OAuth")
        
        try:
            # Click OAuth login button
            browser.find_element_by_link_text(self.login_button_text).click()
            
            # Switch to OAuth provider window if opened
            for handle in browser.window_handles:
                browser.switch_to_window(handle)
            
            # Fill in email/username
            email_elem = browser.find_element_by_name("identifier")
            email_elem.send_keys(self.email)
            browser.find_element_by_id("identifierNext").click()
            
            # Fill in password
            import time
            time.sleep(1)  # Wait for password field to appear
            pass_elem = browser.find_element_by_name("password")
            pass_elem.send_keys(self.password)
            browser.find_element_by_id("passwordNext").click()
            
            # Switch back to main window
            time.sleep(2)  # Wait for redirect
            for handle in browser.window_handles:
                browser.switch_to_window(handle)
        
        except Exception as e:
            raise Exception(f"OAuth authentication with {self.provider} failed: {str(e)}")
    
    def is_authenticated(self, browser):
        """
        Check if OAuth authentication succeeded.
        
        Args:
            browser: Selenium WebDriver instance
            
        Returns:
            bool: True if authenticated
        """
        error_indicators = ['login failed', 'invalid', 'permission denied']
        page_source = browser.page_source.lower()
        
        for indicator in error_indicators:
            if indicator in page_source:
                return False
        
        return True
