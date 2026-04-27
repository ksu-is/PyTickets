# -*- coding: utf-8 -*-
"""Tests for utilities."""
import pytest
from ticketCrawler.utils.helpers import (
    TextHelper, URLHelper, DataHelper, RetryHelper
)


class TestTextHelper:
    """Test text helper functions."""
    
    def test_extract_price_with_currency(self):
        """Test extracting price with currency symbol."""
        assert TextHelper.extract_price("€10.50") == 10.50
        assert TextHelper.extract_price("$25.00") == 25.00
    
    def test_extract_price_with_comma(self):
        """Test extracting price with comma decimal."""
        assert TextHelper.extract_price("€10,50") == 10.50
        assert TextHelper.extract_price("25,99") == 25.99
    
    def test_extract_price_no_decimals(self):
        """Test extracting price without decimals."""
        assert TextHelper.extract_price("€50") == 50.0
        assert TextHelper.extract_price("100") == 100.0
    
    def test_extract_price_from_text(self):
        """Test extracting price from longer text."""
        text = "This ticket costs €45.50 per person"
        assert TextHelper.extract_price(text) == 45.50
    
    def test_extract_price_none(self):
        """Test extracting price when none present."""
        assert TextHelper.extract_price("No price here") is None
        assert TextHelper.extract_price(None) is None
        assert TextHelper.extract_price("") is None
    
    def test_clean_text(self):
        """Test text cleaning."""
        assert TextHelper.clean_text("  hello   world  ") == "hello world"
        assert TextHelper.clean_text("hello\n\nworld") == "hello world"
        assert TextHelper.clean_text(None) == ""
        assert TextHelper.clean_text("") == ""


class TestURLHelper:
    """Test URL helper functions."""
    
    def test_ensure_absolute_url_already_absolute(self):
        """Test with already absolute URL."""
        result = URLHelper.ensure_absolute_url(
            'https://example.com/page',
            'https://base.com'
        )
        assert result == 'https://example.com/page'
    
    def test_ensure_absolute_url_relative(self):
        """Test with relative URL."""
        result = URLHelper.ensure_absolute_url(
            '/page/123',
            'https://example.com'
        )
        assert result == 'https://example.com/page/123'
    
    def test_ensure_absolute_url_relative_no_slash(self):
        """Test with relative URL without leading slash."""
        result = URLHelper.ensure_absolute_url(
            'page/123',
            'https://example.com'
        )
        assert result == 'https://example.com/page/123'
    
    def test_ensure_absolute_url_none(self):
        """Test with None URL."""
        result = URLHelper.ensure_absolute_url(None, 'https://example.com')
        assert result is None


class TestDataHelper:
    """Test data helper functions."""
    
    def test_safe_get_simple(self):
        """Test simple key access."""
        data = {'name': 'John', 'age': 30}
        assert DataHelper.safe_get(data, 'name') == 'John'
        assert DataHelper.safe_get(data, 'age') == 30
    
    def test_safe_get_nested_list(self):
        """Test nested access with list."""
        data = {'user': {'profile': {'name': 'John'}}}
        assert DataHelper.safe_get(data, ['user', 'profile', 'name']) == 'John'
    
    def test_safe_get_nested_dot_notation(self):
        """Test nested access with dot notation."""
        data = {'user': {'profile': {'name': 'John'}}}
        assert DataHelper.safe_get(data, 'user.profile.name') == 'John'
    
    def test_safe_get_missing_key(self):
        """Test accessing missing key."""
        data = {'name': 'John'}
        assert DataHelper.safe_get(data, 'age') is None
        assert DataHelper.safe_get(data, 'age', 25) == 25
    
    def test_safe_get_deep_missing(self):
        """Test accessing missing nested key."""
        data = {'user': {'name': 'John'}}
        assert DataHelper.safe_get(data, 'user.profile.name') is None
    
    def test_flatten_dict(self):
        """Test flattening nested dictionary."""
        data = {
            'user': {
                'name': 'John',
                'profile': {
                    'age': 30
                }
            },
            'status': 'active'
        }
        
        flattened = DataHelper.flatten_dict(data)
        
        assert flattened['user.name'] == 'John'
        assert flattened['user.profile.age'] == 30
        assert flattened['status'] == 'active'


class TestRetryHelper:
    """Test retry helper."""
    
    def test_retry_success_first_attempt(self):
        """Test successful execution on first attempt."""
        def successful_func():
            return 'success'
        
        result = RetryHelper.retry_with_backoff(successful_func, max_attempts=3)
        assert result == 'success'
    
    def test_retry_success_after_failures(self):
        """Test successful execution after retries."""
        attempts = [0]
        
        def sometimes_fails():
            attempts[0] += 1
            if attempts[0] < 3:
                raise ValueError("Not yet")
            return 'success'
        
        result = RetryHelper.retry_with_backoff(sometimes_fails, max_attempts=5)
        assert result == 'success'
        assert attempts[0] == 3
    
    def test_retry_exhausted(self):
        """Test that all retries are exhausted."""
        attempts = [0]
        
        def always_fails():
            attempts[0] += 1
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError):
            RetryHelper.retry_with_backoff(always_fails, max_attempts=3)
        
        assert attempts[0] == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
