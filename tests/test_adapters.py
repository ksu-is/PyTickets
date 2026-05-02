# -*- coding: utf-8 -*-
"""Tests for adapters and authenticators."""
import pytest
from scrapy.http import HtmlResponse

from ticketCrawler.adapters.factory import AdapterFactory
from ticketCrawler.auth.factory import AuthenticatorFactory


class TestAdapterFactory:
    """Test adapter factory."""
    
    def test_list_available_adapters(self):
        """Test listing available adapters."""
        adapters = AdapterFactory.list_adapters()
        assert isinstance(adapters, list)
        assert 'dutch_tickets' in adapters
        assert 'eventim' in adapters
        assert 'ticketmaster' in adapters
        assert 'seatgeek' in adapters
    
    def test_create_dutch_tickets_adapter(self):
        """Test creating Dutch tickets adapter."""
        config = {
            'base_url': 'https://example.com',
            'auth': {'type': 'facebook', 'credentials': {}},
            'selectors': {},
            'proxy_required': False,
            'rate_limit': {'min_delay': 1, 'max_delay': 2}
        }
        
        adapter = AdapterFactory.create_adapter('dutch_tickets', config)
        assert adapter is not None
        assert adapter.base_url == 'https://example.com'
    
    def test_create_eventim_adapter(self):
        """Test creating Eventim adapter."""
        config = {
            'base_url': 'https://example.com',
            'auth': {'type': 'email_password', 'credentials': {}},
            'selectors': {},
            'proxy_required': False,
            'rate_limit': {'min_delay': 1, 'max_delay': 2}
        }
        
        adapter = AdapterFactory.create_adapter('eventim', config)
        assert adapter is not None

    def test_create_ticketmaster_adapter(self):
        config = {
            'base_url': 'https://www.ticketmaster.com',
            'auth': {'type': 'none', 'credentials': {}},
            'selectors': {},
            'proxy_required': False,
            'rate_limit': {'min_delay': 1, 'max_delay': 2}
        }

        adapter = AdapterFactory.create_adapter('ticketmaster', config)
        assert adapter is not None

    def test_create_seatgeek_adapter(self):
        config = {
            'base_url': 'https://seatgeek.com',
            'auth': {'type': 'none', 'credentials': {}},
            'selectors': {},
            'proxy_required': False,
            'rate_limit': {'min_delay': 1, 'max_delay': 2}
        }

        adapter = AdapterFactory.create_adapter('seatgeek', config)
        assert adapter is not None
    
    def test_invalid_adapter_raises_error(self):
        """Test that invalid adapter raises ValueError."""
        with pytest.raises(ValueError):
            AdapterFactory.create_adapter('invalid_site', {})
    
    def test_adapter_has_required_methods(self):
        """Test that adapters have required methods."""
        config = {
            'base_url': 'https://example.com',
            'auth': {'type': 'facebook', 'credentials': {}},
            'selectors': {},
            'proxy_required': False,
            'rate_limit': {'min_delay': 1, 'max_delay': 2}
        }
        
        adapter = AdapterFactory.create_adapter('dutch_tickets', config)
        
        # Check for required methods
        assert hasattr(adapter, 'authenticate')
        assert hasattr(adapter, 'extract_tickets')
        assert hasattr(adapter, 'get_ticket_url')
        assert hasattr(adapter, 'buy_ticket')
        assert hasattr(adapter, 'check_reservation_success')

    def test_ticketmaster_extracts_event_links(self):
        adapter = AdapterFactory.create_adapter('ticketmaster', {
            'base_url': 'https://www.ticketmaster.com',
            'selectors': {},
        })
        response = HtmlResponse(
            url='https://www.ticketmaster.com/search',
            body=b'<a href="/event/ABC123">Concert Tickets</a>',
            encoding='utf-8',
        )

        tickets = adapter.extract_tickets(response)

        assert tickets[0]['url'] == 'https://www.ticketmaster.com/event/ABC123'

    def test_ticketmaster_extracts_discovery_api_events(self):
        adapter = AdapterFactory.create_adapter('ticketmaster', {
            'base_url': 'https://www.ticketmaster.com',
            'selectors': {},
        })
        body = b'''
        {"_embedded":{"events":[{"name":"Concert","url":"https://www.ticketmaster.com/event/ABC123","priceRanges":[{"min":40}],"dates":{"start":{"localDate":"2026-05-02"}}}]}}
        '''
        response = HtmlResponse(
            url='https://app.ticketmaster.com/discovery/v2/events.json',
            body=body,
            encoding='utf-8',
        )

        tickets = adapter.extract_tickets(response)

        assert tickets[0]['url'] == 'https://www.ticketmaster.com/event/ABC123'
        assert tickets[0]['price'] == 40

    def test_ticketmaster_normalizes_public_event_url_to_api_url(self):
        adapter = AdapterFactory.create_adapter('ticketmaster', {
            'base_url': 'https://www.ticketmaster.com',
            'selectors': {},
            'api': {
                'event_endpoint': 'https://app.ticketmaster.com/discovery/v2/events/{event_id}.json',
                'apikey': 'abc123',
            }
        })

        url = adapter.normalize_start_url(
            'https://www.ticketmaster.com/show/event/2D0064529D46D781?landing=c'
        )

        assert url == (
            'https://app.ticketmaster.com/discovery/v2/events/2D0064529D46D781.json'
            '?apikey=abc123'
        )

    def test_ticketmaster_extracts_single_discovery_api_event(self):
        adapter = AdapterFactory.create_adapter('ticketmaster', {
            'base_url': 'https://www.ticketmaster.com',
            'selectors': {},
        })
        body = b'''
        {"name":"Concert","url":"https://www.ticketmaster.com/event/ABC123","priceRanges":[{"min":40}],"dates":{"start":{"dateTime":"2026-05-02T20:00:00Z"}}}
        '''
        response = HtmlResponse(
            url='https://app.ticketmaster.com/discovery/v2/events/ABC123.json',
            body=body,
            encoding='utf-8',
        )

        tickets = adapter.extract_tickets(response)

        assert tickets[0]['url'] == 'https://www.ticketmaster.com/event/ABC123'
        assert tickets[0]['date'] == '2026-05-02T20:00:00Z'

    def test_seatgeek_extracts_next_data_links(self):
        adapter = AdapterFactory.create_adapter('seatgeek', {
            'base_url': 'https://seatgeek.com',
            'selectors': {},
        })
        body = b'''
        <script id="__NEXT_DATA__" type="application/json">
        {"props":{"event":{"title":"Game","url":"https://seatgeek.com/game-tickets","stats":{"lowest_price":25,"listing_count":4}}}}
        </script>
        '''
        response = HtmlResponse(
            url='https://seatgeek.com/search',
            body=body,
            encoding='utf-8',
        )

        tickets = adapter.extract_tickets(response)

        assert tickets[0]['url'] == 'https://seatgeek.com/game-tickets'
        assert tickets[0]['price'] == 25
        assert tickets[0]['quantity'] == 4

    def test_seatgeek_extracts_api_events(self):
        adapter = AdapterFactory.create_adapter('seatgeek', {
            'base_url': 'https://seatgeek.com',
            'selectors': {},
        })
        body = b'''
        {"events":[{"title":"Game","url":"https://seatgeek.com/game-tickets","datetime_local":"2026-05-02T19:00:00","stats":{"lowest_price":25,"listing_count":4}}]}
        '''
        response = HtmlResponse(
            url='https://api.seatgeek.com/2/events',
            body=body,
            encoding='utf-8',
        )

        tickets = adapter.extract_tickets(response)

        assert tickets[0]['url'] == 'https://seatgeek.com/game-tickets'
        assert tickets[0]['price'] == 25


class TestAuthenticatorFactory:
    """Test authenticator factory."""
    
    def test_list_available_authenticators(self):
        """Test listing available authenticators."""
        auths = AuthenticatorFactory.list_authenticators()
        assert 'facebook' in auths
        assert 'email_password' in auths
        assert 'oauth' in auths
    
    def test_create_facebook_authenticator(self):
        """Test creating Facebook authenticator."""
        config = {
            'type': 'facebook',
            'credentials': {
                'email': 'test@example.com',
                'password': 'testpass'
            }
        }
        
        auth = AuthenticatorFactory.create_authenticator('facebook', config)
        assert auth is not None
    
    def test_create_email_password_authenticator(self):
        """Test creating email/password authenticator."""
        config = {
            'type': 'email_password',
            'credentials': {
                'email': 'test@example.com',
                'password': 'testpass'
            }
        }
        
        auth = AuthenticatorFactory.create_authenticator('email_password', config)
        assert auth is not None
    
    def test_invalid_authenticator_raises_error(self):
        """Test that invalid authenticator raises ValueError."""
        with pytest.raises(ValueError):
            AuthenticatorFactory.create_authenticator('invalid_type', {})


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
