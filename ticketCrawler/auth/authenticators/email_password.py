# -*- coding: utf-8 -*-
"""Email/password direct login authenticator."""
from .base_authenticator import BaseAuthenticator


class EmailPasswordAuthenticator(BaseAuthenticator):
    """Authenticator using direct email/password login."""
    
    def __init__(self, config):
        """Initialize email/password authenticator."""
        super().__init__(config)
        self.email = self.credentials.get('email')
        self.password = self.credentials.get('password')
        self.email_field = self.credentials.get('email_field_name', 'email')
        self.password_field = self.credentials.get('password_field_name', 'password')
        self.login_button = self.credentials.get('login_button_selector', 'button[type="submit"]')
    
    def authenticate(self, browser):
        """
        Authenticate using direct email/password login.
        
        Args:
            browser: Selenium WebDriver instance
            
        Raises:
            Exception: If authentication fails
        """
        if not self.email or not self.password:
            raise ValueError("Email and password credentials required")
        
        try:
            # Fill in email
            email_elem = browser.find_element_by_name(self.email_field)
            email_elem.clear()
            email_elem.send_keys(self.email)
            
            # Fill in password
            pass_elem = browser.find_element_by_name(self.password_field)
            pass_elem.clear()
            pass_elem.send_keys(self.password)
            
            # Click login button
            if self.login_button.startswith('button'):
                browser.find_element_by_css_selector(self.login_button).click()
            else:
                browser.find_element_by_id(self.login_button).click()
        
        except Exception as e:
            raise Exception(f"Email/password authentication failed: {str(e)}")
    
    def is_authenticated(self, browser):
        """
        Check if login was successful by looking for logout link or checking redirect.
        
        Args:
            browser: Selenium WebDriver instance
            
        Returns:
            bool: True if authenticated
        """
        # Generic check - can be overridden per site
        error_indicators = ['Invalid credentials', 'Login failed', 'incorrect password']
        page_source = browser.page_source.lower()
        
        for indicator in error_indicators:
            if indicator.lower() in page_source:
                return False
        
        return True
