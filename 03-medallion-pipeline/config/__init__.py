# Medallion Pipeline Configuration
# 
# This package contains configuration for the streaming medallion pipeline.
#
# Modules:
#   - pipeline_config.yaml: Runtime pipeline configuration
#
# NOTE: master_data.py has been moved to 00-data/ for centralized data generation.
# For master data imports, add 00-data/ to sys.path and import from master_data directly.

import os
from pathlib import Path
from typing import Dict, Any, Optional

# -----------------------------------------------------------------------------
# Pipeline Configuration Loader
# -----------------------------------------------------------------------------

_config_cache: Optional[Dict[str, Any]] = None

def load_pipeline_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load pipeline configuration from YAML file.
    
    Args:
        config_path: Optional path to config file. If not provided,
                     looks for pipeline_config.yaml in the config directory.
    
    Returns:
        Dictionary with pipeline configuration.
    """
    global _config_cache
    
    if _config_cache is not None and config_path is None:
        return _config_cache
    
    import yaml
    
    if config_path is None:
        # Find config relative to this file
        config_dir = Path(__file__).parent
        config_path = config_dir / "pipeline_config.yaml"
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    if config_path is None:
        _config_cache = config
    
    return config


def get_pipeline_config() -> Dict[str, Any]:
    """Get cached pipeline configuration."""
    return load_pipeline_config()


def get_catalog() -> str:
    """Get Unity Catalog name from config."""
    return get_pipeline_config().get('catalog', 'juan_dev')


def get_schema() -> str:
    """Get schema name from config."""
    return get_pipeline_config().get('schema', 'retail')


def get_volume_path(source: str) -> str:
    """
    Get volume path for a specific source.
    
    Args:
        source: Source name (pos, ecommerce, inventory, clickstream, etc.)
    
    Returns:
        Full volume path for the source.
    """
    config = get_pipeline_config()
    sources = config.get('volumes', {}).get('sources', {})
    
    if source in sources:
        return sources[source]
    
    # Fallback to base_path + source
    base = config.get('volumes', {}).get('base_path', '/Volumes/juan_dev/retail/data')
    return f"{base}/{source}"


def get_generator_config(generator_name: str) -> Dict[str, Any]:
    """
    Get configuration for a specific generator.
    
    Args:
        generator_name: Generator name (pos, ecommerce, inventory, clickstream, etc.)
    
    Returns:
        Dictionary with generator-specific configuration.
    """
    config = get_pipeline_config()
    return config.get('generators', {}).get(generator_name, {})


def get_autoloader_config() -> Dict[str, Any]:
    """Get Auto Loader configuration."""
    return get_pipeline_config().get('autoloader', {})


# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------
# NOTE: master_data.py has been moved to 00-data/ alongside generators/
# For master data imports, add 00-data/ to sys.path and import from master_data directly

__all__ = [
    # Pipeline Configuration
    'load_pipeline_config', 'get_pipeline_config',
    'get_catalog', 'get_schema', 'get_volume_path',
    'get_generator_config', 'get_autoloader_config',
]
