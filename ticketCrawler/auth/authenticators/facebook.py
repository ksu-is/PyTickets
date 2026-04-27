# -*- coding: utf-8 -*-
"""Facebook OAuth authenticator."""
from .base_authenticator import BaseAuthenticator


class FacebookAuthenticator(BaseAuthenticator):
    """Authenticator using Facebook OAuth."""
    
    def __init__(self, config):
        """Initialize Facebook authenticator."""
        super().__init__(config)
        self.email = self.credentials.get('email')
        self.password = self.credentials.get('password')
    
    def authenticate(self, browser):
        """
        Authenticate using Facebook login flow.
        
        Args:
            browser: Selenium WebDriver instance
            
        Raises:
            Exception: If authentication fails
        """
        if not self.email or not self.password:
            raise ValueError("Facebook credentials (email, password) required")
        
        try:
            # Click login link
            browser.find_element_by_link_text('Inloggen').click()
            
            # Switch to Facebook login window if it opened
            for handle in browser.window_handles:
                browser.switch_to_window(handle)
            
            # Fill in credentials
            email_elem = browser.find_element_by_name("email")
            email_elem.send_keys(self.email)
            
            pass_elem = browser.find_element_by_name("pass")
            pass_elem.send_keys(self.password)
            
            browser.find_element_by_name('login').click()
            
            # Switch back to main window
            for handle in browser.window_handles:
                browser.switch_to_window(handle)
        
        except Exception as e:
            raise Exception(f"Facebook authentication failed: {str(e)}")
    
    def is_authenticated(self, browser):
        """
        Check if Facebook authentication succeeded.
        
        Args:
            browser: Selenium WebDriver instance
            
        Returns:
            bool: True if authenticated
        """
        error_text = "Je hebt ons geen toegang gegeven tot je Facebook account"
        return error_text not in browser.page_source
