# -*- coding: utf-8 -*-
"""Factory for creating site adapters."""
from .site_adapters.dutch_tickets import DutchTicketsAdapter
from .site_adapters.eventim import EventimAdapter


class AdapterFactory:
    """Factory for creating site-specific adapters."""
    
    # Mapping of site names to adapter classes
    ADAPTERS = {
        'dutch_tickets': DutchTicketsAdapter,
        'eventim': EventimAdapter,
    }
    
    @classmethod
    def create_adapter(cls, site_name, config):
        """
        Create an adapter instance for the specified site.
        
        Args:
            site_name (str): Name of the site configuration
            config (dict): Site configuration dictionary
            
        Returns:
            BaseAdapter: Configured adapter instance
            
        Raises:
            ValueError: If site adapter not found
        """
        if site_name not in cls.ADAPTERS:
            available = ', '.join(cls.ADAPTERS.keys())
            raise ValueError(f"Unknown site: {site_name}. Available: {available}")
        
        adapter_class = cls.ADAPTERS[site_name]
        return adapter_class(config)
    
    @classmethod
    def register_adapter(cls, site_name, adapter_class):
        """
        Register a new site adapter.
        
        Args:
            site_name (str): Name of the site
            adapter_class: Adapter class (must inherit from BaseAdapter)
        """
        cls.ADAPTERS[site_name] = adapter_class
    
    @classmethod
    def list_adapters(cls):
        """List all registered adapters."""
        return list(cls.ADAPTERS.keys())
