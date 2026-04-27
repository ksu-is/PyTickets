# -*- coding: utf-8 -*-
"""
Example usage of the refactored PyTickets system.

This demonstrates how to use the new modular architecture with
adapters, authenticators, filters, and notifications.
"""

from ticketCrawler.config.config_loader import ConfigLoader
from ticketCrawler.adapters.factory import AdapterFactory
from ticketCrawler.auth.factory import AuthenticatorFactory
from ticketCrawler.filters.factory import FilterFactory
from ticketCrawler.notifications.manager import NotificationManager, NotificationFactory


def example_basic_usage():
    """Example 1: Basic usage with default configuration."""
    
    # Load site configuration
    config_loader = ConfigLoader()
    site_config = config_loader.get_config('dutch_tickets')
    
    # Create site adapter
    adapter = AdapterFactory.create_adapter('dutch_tickets', site_config)
    print(f"Adapter: {adapter}")
    print(f"Proxy required: {adapter.is_proxy_required()}")
    print(f"Rate limits: {adapter.get_rate_limits()}")


def example_with_authentication():
    """Example 2: Using authenticator."""
    
    config_loader = ConfigLoader()
    site_config = config_loader.get_config('dutch_tickets')
    
    # Get authenticator from config
    auth_config = site_config.get('auth', {})
    auth_type = auth_config.get('type')
    
    # Create authenticator
    authenticator = AuthenticatorFactory.create_authenticator(auth_type, auth_config)
    print(f"Authenticator type: {auth_type}")
    print(f"Authenticator: {authenticator}")


def example_with_filters():
    """Example 3: Creating and using filters."""
    
    from ticketCrawler.filters.factory import FilterFactory
    
    # Create individual filters
    price_filter = FilterFactory.create_filter(
        'price',
        min_price=10.0,
        max_price=100.0
    )
    
    seat_filter = FilterFactory.create_filter(
        'seat_type',
        seat_types=['floor', 'vip'],
        exclude_seat_types=['balcony']
    )
    
    date_filter = FilterFactory.create_filter(
        'date',
        start_date='2026-05-01',
        end_date='2026-12-31'
    )
    
    # Combine filters
    combined = FilterFactory.create_combined_filter([
        {'type': 'price', 'min_price': 10, 'max_price': 100},
        {'type': 'seat_type', 'seat_types': ['floor', 'vip']},
    ], require_all=True)
    
    print(f"Price filter: {price_filter}")
    print(f"Seat filter: {seat_filter}")
    print(f"Combined filter: {combined}")
    
    # Test filtering
    test_tickets = [
        {'price': 25.00, 'seat_type': 'floor', 'date': '2026-06-15', 'quantity': 2},
        {'price': 150.00, 'seat_type': 'vip', 'date': '2026-06-15', 'quantity': 1},
        {'price': 50.00, 'seat_type': 'balcony', 'date': '2026-06-15', 'quantity': 3},
    ]
    
    print("\nOriginal tickets:")
    for t in test_tickets:
        print(f"  {t}")
    
    print("\nFiltered tickets:")
    filtered = combined.filter_tickets(test_tickets)
    for t in filtered:
        print(f"  {t}")


def example_with_notifications():
    """Example 4: Setting up notifications."""
    
    # Create notification manager
    manager = NotificationManager()
    
    # Add Telegram notifier
    telegram_config = {
        'token': 'YOUR_TELEGRAM_BOT_TOKEN',
        'chat_id': 'YOUR_CHAT_ID'
    }
    telegram_notifier = NotificationFactory.create_notifier('telegram', telegram_config)
    manager.add_notifier(telegram_notifier)
    
    # Add Email notifier (SMTP)
    email_config = {
        'provider': 'smtp',
        'sender': 'your-email@gmail.com',
        'recipient': 'recipient@example.com',
        'smtp_host': 'smtp.gmail.com',
        'smtp_port': 587,
        'smtp_user': 'your-email@gmail.com',
        'smtp_password': 'your-app-password'
    }
    email_notifier = NotificationFactory.create_notifier('email', email_config)
    manager.add_notifier(email_notifier)
    
    # Add Webhook notifier
    webhook_config = {
        'url': 'https://example.com/webhook/tickets',
        'method': 'POST',
        'headers': {'Authorization': 'Bearer YOUR_TOKEN'}
    }
    webhook_notifier = NotificationFactory.create_notifier('webhook', webhook_config)
    manager.add_notifier(webhook_notifier)
    
    print(f"Notification manager: {manager}")
    
    # Send notification (would fail with placeholder credentials)
    # results = manager.notify("Test message")
    # print(f"Notification results: {results}")


def example_register_custom_adapter():
    """Example 5: Registering a custom site adapter."""
    
    from ticketCrawler.adapters.base_adapter import BaseAdapter
    from ticketCrawler.adapters.factory import AdapterFactory
    
    class CustomSiteAdapter(BaseAdapter):
        """Example custom adapter for a new ticket site."""
        
        def authenticate(self, browser):
            """Custom authentication logic."""
            pass
        
        def check_tickets_available(self, response):
            """Custom logic to check tickets."""
            return True
        
        def get_first_sold_ticket_url(self, response):
            """Custom logic to get first URL."""
            return "https://example.com/tickets/sold"
        
        def extract_tickets(self, response):
            """Custom extraction logic."""
            return []
        
        def get_ticket_url(self, ticket_element):
            """Custom URL extraction."""
            return "https://example.com/ticket/123"
        
        def check_ticket_available(self, browser):
            """Check if ticket is available."""
            return True
        
        def buy_ticket(self, browser):
            """Click buy button."""
            return True
        
        def check_reservation_success(self, browser):
            """Check if reservation succeeded."""
            return True
    
    # Register custom adapter
    AdapterFactory.register_adapter('custom_site', CustomSiteAdapter)
    
    print(f"Available adapters: {AdapterFactory.list_adapters()}")


def example_list_available_components():
    """Example 6: List available components."""
    
    print("Available adapters:")
    print(f"  {AdapterFactory.list_adapters()}")
    
    print("\nAvailable authenticators:")
    print(f"  {AuthenticatorFactory.list_authenticators()}")
    
    print("\nAvailable filters:")
    print(f"  {FilterFactory.list_filters()}")
    
    print("\nAvailable notifiers:")
    from ticketCrawler.notifications.manager import NotificationFactory
    print(f"  {NotificationFactory.list_notifiers()}")


if __name__ == '__main__':
    print("=" * 60)
    print("PyTickets Refactored System - Usage Examples")
    print("=" * 60)
    
    print("\n[Example 1] Basic Usage")
    print("-" * 60)
    try:
        example_basic_usage()
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n[Example 2] With Authentication")
    print("-" * 60)
    try:
        example_with_authentication()
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n[Example 3] With Filters")
    print("-" * 60)
    try:
        example_with_filters()
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n[Example 4] With Notifications")
    print("-" * 60)
    try:
        example_with_notifications()
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n[Example 5] Custom Adapter")
    print("-" * 60)
    try:
        example_register_custom_adapter()
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n[Example 6] Available Components")
    print("-" * 60)
    try:
        example_list_available_components()
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 60)
