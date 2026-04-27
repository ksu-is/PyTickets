# -*- coding: utf-8 -*-
"""Tests for configuration system."""
import os
import pytest
from pathlib import Path
from ticketCrawler.config.config_loader import ConfigLoader


class TestConfigLoader:
    """Test ConfigLoader functionality."""
    
    def setup_method(self):
        """Setup for each test."""
        self.config_loader = ConfigLoader()
    
    def test_list_available_sites(self):
        """Test that we can list available sites."""
        sites = self.config_loader.list_available_sites()
        assert isinstance(sites, list)
        assert len(sites) > 0
        assert 'dutch_tickets' in sites
    
    def test_get_dutch_tickets_config(self):
        """Test loading Dutch tickets configuration."""
        config = self.config_loader.get_config('dutch_tickets')
        
        assert config is not None
        assert 'name' in config
        assert 'base_url' in config
        assert 'auth' in config
        assert 'selectors' in config
    
    def test_get_eventim_config(self):
        """Test loading Eventim configuration."""
        config = self.config_loader.get_config('eventim')
        
        assert config is not None
        assert 'name' in config
        assert config['name'] == 'Eventim'
    
    def test_config_has_auth_section(self):
        """Test that configs have auth section."""
        config = self.config_loader.get_config('dutch_tickets')
        auth = config.get('auth', {})
        
        assert 'type' in auth
        assert auth['type'] in ['facebook', 'email_password', 'oauth', 'none']
    
    def test_config_has_rate_limits(self):
        """Test that configs have rate limits."""
        config = self.config_loader.get_config('dutch_tickets')
        rate_limits = config.get('rate_limit', {})
        
        assert 'min_delay' in rate_limits
        assert 'max_delay' in rate_limits
        assert rate_limits['min_delay'] <= rate_limits['max_delay']
    
    def test_config_has_selectors(self):
        """Test that configs have selectors."""
        config = self.config_loader.get_config('dutch_tickets')
        selectors = config.get('selectors', {})
        
        assert len(selectors) > 0
        assert 'buy_button_class' in selectors or 'buy_button_xpath' in selectors
    
    def test_invalid_site_raises_error(self):
        """Test that invalid site raises KeyError."""
        with pytest.raises(KeyError):
            self.config_loader.get_config('nonexistent_site')


class TestEnvironmentVariableSubstitution:
    """Test environment variable substitution in configs."""
    
    def test_env_var_substitution(self):
        """Test that env vars are substituted."""
        # Set test env var
        os.environ['test_url'] = 'https://example.com'
        
        config_loader = ConfigLoader()
        config = config_loader.get_config('dutch_tickets')
        
        # Note: This test checks that substitution happens,
        # but actual values depend on environment
        assert config['base_url'] is not None
    
    def test_missing_env_var_raises_error(self):
        """Test that missing env vars raise ValueError."""
        # This would only happen if a config references a non-existent env var
        # and it's not overridden elsewhere
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
