# -*- coding: utf-8 -*-
"""Tests for adapters and authenticators."""
import pytest
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
