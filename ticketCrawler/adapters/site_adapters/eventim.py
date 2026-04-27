# -*- coding: utf-8 -*-
"""Adapter for Eventim ticket website."""
from ..base_adapter import BaseAdapter


class EventimAdapter(BaseAdapter):
    """Adapter for Eventim ticket booking platform."""
    
    def __init__(self, config):
        """Initialize Eventim adapter."""
        super().__init__(config)
        self.selectors = config.get('selectors', {})
    
    def authenticate(self, browser):
        """
        Authenticate using email/password login.
        
        Args:
            browser: Selenium WebDriver instance
            
        Raises:
            Exception: If authentication fails
        """
        try:
            # Get selectors
            email_field = self.selectors.get('email_field_name', 'loginEmail')
            password_field = self.selectors.get('password_field_name', 'password')
            login_button = self.selectors.get('login_button_selector', 'button.btn-login')
            
            # Fill credentials
            email_elem = browser.find_element_by_name(email_field)
            email_elem.send_keys(self.config['auth']['credentials']['email'])
            
            pass_elem = browser.find_element_by_name(password_field)
            pass_elem.send_keys(self.config['auth']['credentials']['password'])
            
            # Click login
            browser.find_element_by_css_selector(login_button).click()
            
            import time
            time.sleep(2)  # Wait for login
        
        except Exception as e:
            raise Exception(f"Eventim authentication failed: {str(e)}")
    
    def check_tickets_available(self, response):
        """
        Check if tickets are available on the page.
        
        Returns:
            bool: True if tickets available
        """
        body = response.body if hasattr(response, 'body') else response
        no_tickets_text = self.selectors.get('no_tickets_text', [])
        
        for text in no_tickets_text:
            if text in body:
                return False
        
        return True
    
    def get_first_sold_ticket_url(self, response):
        """
        For Eventim, we don't need a specific first sold ticket URL.
        We work with event listings directly.
        
        Returns:
            str: URL of events listing page or None
        """
        # Eventim doesn't have sold ticket section like Dutch site
        # Return the events page directly
        return self.base_url
    
    def extract_tickets(self, response):
        """
        Extract ticket events from response.
        
        Returns:
            list: List of event elements
        """
        xpath = self.selectors.get('ticket_array_xpath', "//div[@class='eventitem']")
        return response.xpath(xpath)
    
    def get_ticket_url(self, ticket_element):
        """
        Extract URL from a ticket event element.
        
        Args:
            ticket_element: Scrapy selector for individual event
            
        Returns:
            str: Full URL of the event
        """
        xpath = self.selectors.get('ticket_link_xpath', 'a.eventlink/@href')
        link = ticket_element.xpath(xpath).extract_first()
        
        if link:
            # Handle relative URLs
            if not link.startswith('http'):
                return self.base_url.rstrip('/') + '/' + link.lstrip('/')
            return link
        
        return None
    
    def check_ticket_available(self, browser):
        """
        Check if event has available tickets.
        
        Args:
            browser: Selenium WebDriver instance
            
        Returns:
            bool: True if tickets available
        """
        # Check if buy button is present and enabled
        try:
            buy_button_class = self.selectors.get('buy_button_class', 'btn-buy-ticket')
            button = browser.find_element_by_class_name(buy_button_class)
            return button.is_enabled()
        except:
            return False
    
    def buy_ticket(self, browser):
        """
        Click the buy/add to cart button.
        
        Args:
            browser: Selenium WebDriver instance
            
        Returns:
            bool: True if button clicked successfully
        """
        import time
        try:
            # Try XPath first
            buy_button_xpath = self.selectors.get('buy_button_xpath', "//button[contains(@class, 'buy')]")
            button = browser.find_element_by_xpath(buy_button_xpath)
            button.click()
            time.sleep(3)  # Wait for action
            return True
        except Exception as e:
            print(f"Error clicking buy button: {str(e)}")
            return False
    
    def check_reservation_success(self, browser):
        """
        Check if ticket was successfully added to cart/reserved.
        
        Args:
            browser: Selenium WebDriver instance
            
        Returns:
            bool: True if successful
        """
        success_indicators = self.selectors.get('success_indicators', [])
        page_source = browser.page_source
        
        for indicator in success_indicators:
            if indicator in page_source:
                return True
        
        return False
    
    def is_rate_limited(self, response):
        """
        Check if we've been rate limited or blocked.
        
        Args:
            response: Page content
            
        Returns:
            bool: True if rate limited
        """
        # Eventim specific rate limit indicators
        rate_limit_texts = [
            'Too many requests',
            'Please wait',
            'Access denied temporarily',
            'Retry-After'
        ]
        
        body = response.body if hasattr(response, 'body') else response
        
        for text in rate_limit_texts:
            if text in body:
                return True
        
        return False
    
    def has_error(self, browser):
        """
        Check for any error on the page.
        
        Args:
            browser: Selenium WebDriver instance
            
        Returns:
            str: Error type if found, None otherwise
        """
        error_indicators = self.selectors.get('error_indicators', {})
        page_source = browser.page_source
        
        for error_type, error_text in error_indicators.items():
            if error_text in page_source:
                return error_type
        
        return None
