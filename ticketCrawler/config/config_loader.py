# -*- coding: utf-8 -*-
import json
import os
from copy import deepcopy
from pathlib import Path


class ConfigLoader:
    """Loads and manages site configurations with environment variable substitution."""
    
    def __init__(self, config_dir=None):
        """
        Initialize ConfigLoader.
        
        Args:
            config_dir: Path to config directory. Defaults to project configs/sites/
        """
        if config_dir is None:
            # Default to project configs directory
            project_root = Path(__file__).parent.parent.parent
            config_dir = project_root / "configs" / "sites"
        
        self.config_dir = Path(config_dir)
        self._configs = {}
        self._load_all_configs()
    
    def _load_all_configs(self):
        """Load all JSON configs from the config directory."""
        if not self.config_dir.exists():
            raise FileNotFoundError(f"Config directory not found: {self.config_dir}")
        
        for config_file in self.config_dir.glob("*.json"):
            config_name = config_file.stem
            self._configs[config_name] = self._load_config_file(config_file)
    
    def _load_config_file(self, file_path):
        """Load and parse a single config file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _substitute_env_vars(self, obj):
        """Recursively substitute environment variable references in config."""
        if isinstance(obj, str):
            if obj.startswith("env_optional:"):
                env_var = obj[13:]
                return os.environ.get(env_var)
            if obj.startswith("env:"):
                env_var = obj[4:]  # Remove "env:" prefix
                if env_var not in os.environ:
                    raise ValueError(f"Environment variable not found: {env_var}")
                return os.environ[env_var]
            return obj
        elif isinstance(obj, dict):
            return {k: self._substitute_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_env_vars(item) for item in obj]
        return obj
    
    def get_config(self, site_name):
        """
        Get configuration for a specific site.
        
        Args:
            site_name: Name of the site config to load
            
        Returns:
            dict: Site configuration
            
        Raises:
            KeyError: If site configuration not found
        """
        if site_name not in self._configs:
            raise KeyError(f"Site configuration not found: {site_name}. Available: {list(self._configs.keys())}")
        
        return self._substitute_env_vars(deepcopy(self._configs[site_name]))
    
    def list_available_sites(self):
        """Return list of available site configurations."""
        return list(self._configs.keys())
    
    def reload_config(self, site_name):
        """Reload a specific site configuration."""
        config_file = self.config_dir / f"{site_name}.json"
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")
        
        self._configs[site_name] = self._load_config_file(config_file)
        return self._substitute_env_vars(deepcopy(self._configs[site_name]))
