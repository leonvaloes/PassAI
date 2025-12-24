"""
Configuration loader utility
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file and environment variables
    
    Args:
        config_path: Path to config file (default: config/config.yaml)
        
    Returns:
        Configuration dictionary
    """
    # Load environment variables
    load_dotenv()
    
    # Default config path
    if config_path is None:
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / "config" / "config.yaml"
        
        # Fallback to example if config doesn't exist
        if not config_path.exists():
            config_path = project_root / "config" / "config.example.yaml"
    
    # Load YAML
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Replace environment variables
    config = _replace_env_vars(config)
    
    # Add config path for reference
    config['config_path'] = str(config_path)
    
    return config


def _replace_env_vars(obj: Any) -> Any:
    """
    Recursively replace ${VAR} patterns with environment variables
    """
    if isinstance(obj, dict):
        return {k: _replace_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_replace_env_vars(item) for item in obj]
    elif isinstance(obj, str):
        if obj.startswith('${') and obj.endswith('}'):
            var_name = obj[2:-1]
            return os.environ.get(var_name, obj)
    return obj


def get_nested_config(config: Dict, path: str, default: Any = None) -> Any:
    """
    Get nested configuration value using dot notation
    
    Example:
        get_nested_config(config, 'llm.local.model')
        
    Args:
        config: Configuration dictionary
        path: Dot-separated path to value
        default: Default value if not found
        
    Returns:
        Configuration value or default
    """
    keys = path.split('.')
    value = config
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    
    return value
