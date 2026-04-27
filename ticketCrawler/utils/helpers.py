# -*- coding: utf-8 -*-
"""Helper utilities."""
import random
import time
from typing import Optional, Any


class RetryHelper:
    """Helper for retry logic with exponential backoff."""
    
    @staticmethod
    def retry_with_backoff(
        func,
        max_attempts=3,
        initial_delay=1,
        max_delay=60,
        backoff_factor=2,
        exception_types=(Exception,)
    ):
        """
        Execute function with retry and exponential backoff.
        
        Args:
            func: Function to execute
            max_attempts: Maximum number of attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay between retries
            backoff_factor: Multiplier for delay each attempt
            exception_types: Tuple of exception types to catch
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries exhausted
        """
        delay = initial_delay
        last_exception = None
        
        for attempt in range(1, max_attempts + 1):
            try:
                return func()
            except exception_types as e:
                last_exception = e
                
                if attempt < max_attempts:
                    # Add jitter to delay
                    jitter = random.uniform(0.8, 1.2)
                    actual_delay = min(delay * jitter, max_delay)
                    
                    print(f"Attempt {attempt} failed: {str(e)}. Retrying in {actual_delay:.1f}s...")
                    time.sleep(actual_delay)
                    delay *= backoff_factor
        
        raise last_exception


class URLHelper:
    """Helper functions for URL handling."""
    
    @staticmethod
    def ensure_absolute_url(url, base_url):
        """
        Convert relative URL to absolute if needed.
        
        Args:
            url (str): URL (relative or absolute)
            base_url (str): Base URL for relative URLs
            
        Returns:
            str: Absolute URL
        """
        if not url:
            return None
        
        if url.startswith('http://') or url.startswith('https://'):
            return url
        
        # Remove leading slash for joining
        if url.startswith('/'):
            url = url[1:]
        
        # Remove trailing slash from base
        base = base_url.rstrip('/')
        
        return f"{base}/{url}"
    
    @staticmethod
    def parse_query_param(url, param_name):
        """
        Extract query parameter from URL.
        
        Args:
            url (str): URL with query string
            param_name (str): Parameter name to extract
            
        Returns:
            str: Parameter value or None
        """
        try:
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            return params.get(param_name, [None])[0]
        except Exception:
            return None


class TextHelper:
    """Helper functions for text processing."""
    
    @staticmethod
    def extract_price(text):
        """
        Extract price from text.
        
        Args:
            text (str): Text containing price
            
        Returns:
            float: Extracted price or None
        """
        import re
        
        if not text:
            return None
        
        # Match price patterns: €10.50, $10.50, 10,50 EUR, etc.
        price_pattern = r'[\€\$]?\s?(\d+[.,]\d{2}|\d+)'
        match = re.search(price_pattern, str(text))
        
        if match:
            price_str = match.group(1).replace(',', '.')
            try:
                return float(price_str)
            except ValueError:
                return None
        
        return None
    
    @staticmethod
    def extract_date(text, date_format='%Y-%m-%d'):
        """
        Extract date from text.
        
        Args:
            text (str): Text containing date
            date_format (str): Expected date format
            
        Returns:
            datetime: Parsed date or None
        """
        from datetime import datetime
        import re
        
        if not text:
            return None
        
        # Try common date patterns
        patterns = [
            r'\d{4}-\d{2}-\d{2}',  # 2026-04-27
            r'\d{2}-\d{2}-\d{4}',  # 27-04-2026
            r'\d{2}/\d{2}/\d{4}',  # 27/04/2026
            r'\d{4}/\d{2}/\d{2}',  # 2026/04/27
        ]
        
        text_str = str(text).strip()
        
        for pattern in patterns:
            match = re.search(pattern, text_str)
            if match:
                date_str = match.group(0)
                try:
                    return datetime.strptime(date_str, date_format)
                except ValueError:
                    # Try other formats
                    for fmt in ['%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d']:
                        try:
                            return datetime.strptime(date_str, fmt)
                        except ValueError:
                            continue
        
        return None
    
    @staticmethod
    def clean_text(text):
        """
        Clean and normalize text.
        
        Args:
            text (str): Text to clean
            
        Returns:
            str: Cleaned text
        """
        if not text:
            return ''
        
        # Remove extra whitespace
        cleaned = ' '.join(str(text).split())
        
        return cleaned.strip()


class DataHelper:
    """Helper functions for data manipulation."""
    
    @staticmethod
    def safe_get(data, keys, default=None):
        """
        Safely get nested dictionary value.
        
        Args:
            data (dict): Dictionary to search
            keys (str or list): Key path (e.g., 'user.profile.name' or ['user', 'profile', 'name'])
            default: Default value if key not found
            
        Returns:
            Value or default
        """
        if isinstance(keys, str):
            keys = keys.split('.')
        
        current = data
        
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return default
            
            if current is None:
                return default
        
        return current
    
    @staticmethod
    def flatten_dict(data, parent_key='', sep='.'):
        """
        Flatten nested dictionary.
        
        Args:
            data (dict): Dictionary to flatten
            parent_key (str): Parent key prefix
            sep (str): Separator for keys
            
        Returns:
            dict: Flattened dictionary
        """
        items = []
        
        for k, v in data.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(DataHelper.flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        
        return dict(items)
