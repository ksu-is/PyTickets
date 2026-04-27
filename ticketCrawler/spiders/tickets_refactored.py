# -*- coding: utf-8 -*-
"""
Refactored Tickets Spider using modular architecture.

This spider now uses:
- ConfigLoader for site configuration
- Site adapters for website-specific logic
- Authenticators for flexible login methods
- Notification manager for multi-channel alerts
- Filters for ticket filtering
- Loggers for structured logging
"""

import scrapy
import time
import random
from selenium import webdriver
import os

from ticketCrawler.config.config_loader import ConfigLoader
from ticketCrawler.adapters.factory import AdapterFactory
from ticketCrawler.auth.factory import AuthenticatorFactory
from ticketCrawler.filters.factory import FilterFactory
from ticketCrawler.notifications.manager import NotificationManager, NotificationFactory
from ticketCrawler.utils.logger import LoggerFactory
from ticketCrawler.utils.helpers import RetryHelper, URLHelper


class RefactoredTicketsSpider(scrapy.Spider):
    """
    Refactored spider supporting multiple ticket websites with flexible configuration.
    """
    
    name = "tickets_refactored"
    
    custom_settings = {
        "DOWNLOAD_DELAY": 0.25
    }
    
    def __init__(self, site='dutch_tickets', url=None, *args, **kwargs):
        """
        Initialize spider with site configuration.
        
        Args:
            site (str): Site configuration name (e.g., 'dutch_tickets')
            url (str): URL to scrape (can override config)
        """
        super().__init__(*args, **kwargs)
        
        # Setup logging
        LoggerFactory.setup()
        self.logger = LoggerFactory.get_logger(__name__)
        
        self.logger.info(f"Initializing spider for site: {site}")
        
        # Load configuration
        self.config_loader = ConfigLoader()
        self.site_config = self.config_loader.get_config(site)
        self.base_url = self.site_config.get('base_url')
        
        # Create site adapter
        self.adapter = AdapterFactory.create_adapter(site, self.site_config)
        
        # Create authenticator
        auth_config = self.site_config.get('auth', {})
        auth_type = auth_config.get('type', 'none')
        self.authenticator = AuthenticatorFactory.create_authenticator(auth_type, auth_config) if auth_type != 'none' else None
        
        # Setup notification manager
        self.notification_manager = self._setup_notifications()
        
        # Setup filters
        self.ticket_filter = self._setup_filters()
        
        # Initialize Selenium browser
        self.browser = webdriver.Chrome()
        self.browser.get(self.base_url)
        
        # Authenticate if needed
        if self.authenticator:
            self._authenticate()
        
        # Setup URLs
        self.start_urls = [url] if url else []
        self.first_sold_ticket_url = None
        self.successful = False
        self.iteration = 0
    
    def _setup_notifications(self):
        """Setup notification manager from config."""
        manager = NotificationManager()
        
        notifications_config = os.environ.get('NOTIFICATIONS_CONFIG')
        if not notifications_config:
            # Use telegram by default if token available
            token = os.environ.get('telegram_token')
            chat_id = os.environ.get('telegram_chat_id')
            
            if token and chat_id:
                telegram_notifier = NotificationFactory.create_notifier(
                    'telegram',
                    {'token': token, 'chat_id': chat_id}
                )
                manager.add_notifier(telegram_notifier)
        
        return manager
    
    def _setup_filters(self):
        """Setup ticket filters from environment variables."""
        filters_config = []
        
        # Price filter
        min_price = os.environ.get('min_price')
        max_price = os.environ.get('max_price')
        if min_price or max_price:
            filters_config.append({
                'type': 'price',
                'min_price': float(min_price) if min_price else None,
                'max_price': float(max_price) if max_price else None
            })
        
        # Seat type filter
        seat_types = os.environ.get('seat_types')
        if seat_types:
            filters_config.append({
                'type': 'seat_type',
                'seat_types': seat_types.split(',')
            })
        
        if filters_config:
            return FilterFactory.create_combined_filter(filters_config, require_all=True)
        
        return None
    
    def _authenticate(self):
        """Authenticate with the website."""
        try:
            self.logger.info(f"Authenticating with {self.site_config['auth']['type']}")
            self.authenticator.authenticate(self.browser)
            
            if self.authenticator.is_authenticated(self.browser):
                self.logger.info("Authentication successful")
            else:
                self.logger.warning("Authentication may have failed - check browser")
        
        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            raise
    
    def start_requests(self):
        """Generate initial requests."""
        if not self.start_urls:
            self.logger.warning("No URLs provided. Use: scrapy crawl tickets_refactored -a url=<url>")
            return
        
        for url in self.start_urls:
            request = scrapy.Request(
                url=url,
                callback=self.visit_first_sold_ticket,
                dont_filter=True
            )
            yield request
    
    def visit_first_sold_ticket(self, response):
        """
        Find and visit the first sold ticket listing.
        """
        try:
            self.logger.info("Looking for first sold ticket listing")
            self.first_sold_ticket_url = self.adapter.get_first_sold_ticket_url(response)
            
            if self.first_sold_ticket_url:
                self.logger.info(f"Opening: {self.first_sold_ticket_url}")
                request = scrapy.Request(
                    url=self.first_sold_ticket_url,
                    callback=self.parse,
                    dont_filter=True
                )
                yield request
            else:
                self.logger.error("Could not find first sold ticket URL")
                self._save_debug_html(response.body, 'no_sold_tickets.html')
        
        except Exception as e:
            self.logger.error(f"Error in visit_first_sold_ticket: {str(e)}")
            self._save_debug_html(response.body, 'error_visit_sold.html')
    
    def parse(self, response):
        """
        Parse ticket listing page and look for available tickets.
        """
        self.iteration += 1
        self.logger.info(f"Parse iteration #{self.iteration}")
        
        try:
            # Check for no tickets available
            if not self.adapter.check_tickets_available(response.body if hasattr(response, 'body') else response):
                self.logger.info("No tickets available, sleeping before retry")
                
                rate_limits = self.adapter.get_rate_limits()
                sleep_duration = random.uniform(rate_limits['min_delay'], rate_limits['max_delay'])
                time.sleep(sleep_duration)
                
                yield scrapy.Request(
                    url=self.first_sold_ticket_url,
                    callback=self.parse,
                    dont_filter=True
                )
                return
            
            # Check for rate limiting
            if self.adapter.is_rate_limited(response.body if hasattr(response, 'body') else response):
                self.logger.warning("Rate limited! Notifying and pausing")
                self.notification_manager.notify("Rate limited. Waiting for manual reset.")
                raw_input('Press ENTER to continue after rate limit passes')
                
                yield scrapy.Request(
                    url=self.first_sold_ticket_url,
                    callback=self.parse,
                    dont_filter=True
                )
                return
            
            # Found tickets!
            self.logger.info("Tickets found!")
            self.browser.get(response.url)
            
            tickets = self.adapter.extract_tickets(response)
            self.logger.info(f"Found {len(tickets)} ticket(s)")
            
            for ticket in tickets:
                if self.successful:
                    break
                
                try:
                    ticket_url = self.adapter.get_ticket_url(ticket)
                    self.logger.info(f"Trying ticket: {ticket_url}")
                    
                    self.browser.get(ticket_url)
                    
                    # Check if still available
                    if not self.adapter.check_ticket_available(self.browser):
                        self.logger.info("Ticket already reserved, skipping")
                        continue
                    
                    # Buy ticket
                    if self.adapter.buy_ticket(self.browser):
                        # Check if reservation was successful
                        if self.adapter.check_reservation_success(self.browser):
                            self.logger.info("✓ Ticket successfully reserved!")
                            self.successful = True
                            
                            # Send notification
                            ticket_data = {
                                'url': ticket_url,
                                'site': self.site_config.get('name', 'Unknown')
                            }
                            self.notification_manager.notify_ticket_found(ticket_data)
                        
                        elif self.adapter.has_facebook_error(self.browser):
                            self.logger.error("Facebook authentication error")
                        
                        else:
                            self.logger.warning("Unknown error after clicking buy button")
                            self.browser.save_screenshot('error_unknown.png')
                    
                except Exception as e:
                    self.logger.error(f"Error processing ticket: {str(e)}")
                    continue
        
        except Exception as e:
            self.logger.error(f"Error in parse: {str(e)}")
            self._save_debug_html(response.body, 'error_parse.html')
    
    def _save_debug_html(self, html_body, filename='debug.html'):
        """Save HTML for debugging."""
        try:
            with open(filename, 'wb') as f:
                f.write(html_body)
            self.logger.info(f"Saved debug HTML: {filename}")
        except Exception as e:
            self.logger.warning(f"Could not save debug HTML: {str(e)}")
    
    def closed(self, reason):
        """Clean up when spider closes."""
        if self.browser:
            self.browser.quit()
        
        status = "✓ Successful" if self.successful else "✗ No tickets reserved"
        self.logger.info(f"Spider closed. Status: {status}. Reason: {reason}")
