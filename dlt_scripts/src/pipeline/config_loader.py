#!/usr/bin/env python3

import os
import re
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import ValidationError

from .config_models import ConfigurationModel


class ConfigurationError(Exception):
    """Custom exception for configuration-related errors."""
    pass


class ConfigLoader:
    """Configuration loader with environment variable substitution and validation."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the configuration loader.
        
        Args:
            config_dir: Directory containing configuration files. Defaults to 'config' in script directory.
        """
        if config_dir is None:
            script_dir = Path(__file__).parent.parent.parent
            config_dir = script_dir / "config"
        
        self.config_dir = Path(config_dir)
        self.env_pattern = re.compile(r'\$\{([^}]+)\}')
    
    def substitute_environment_variables(self, value: Any) -> Any:
        """
        Recursively substitute environment variables in configuration values.
        
        Supports format: ${VAR_NAME} or ${VAR_NAME:default_value}
        
        Args:
            value: Configuration value that may contain environment variables
            
        Returns:
            Value with environment variables substituted
        """
        if isinstance(value, str):
            def replace_env_var(match):
                var_spec = match.group(1)
                if ':' in var_spec:
                    var_name, default_value = var_spec.split(':', 1)
                else:
                    var_name, default_value = var_spec, None
                
                env_value = os.getenv(var_name.strip())
                if env_value is not None:
                    return env_value
                elif default_value is not None:
                    return default_value
                else:
                    raise ConfigurationError(
                        f"Environment variable '{var_name}' is not set and no default provided"
                    )
            
            return self.env_pattern.sub(replace_env_var, value)
        
        elif isinstance(value, dict):
            return {k: self.substitute_environment_variables(v) for k, v in value.items()}
        
        elif isinstance(value, list):
            return [self.substitute_environment_variables(item) for item in value]
        
        else:
            return value
    
    def load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Load and parse a YAML file.
        
        Args:
            file_path: Path to the YAML file
            
        Returns:
            Parsed YAML content as dictionary
            
        Raises:
            ConfigurationError: If file cannot be loaded or parsed
        """
        try:
            if not file_path.exists():
                raise ConfigurationError(f"Configuration file not found: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
                
            if content is None:
                content = {}
                
            return content
            
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Error parsing YAML file {file_path}: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading configuration file {file_path}: {e}")
    
    def merge_configurations(self, base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two configuration dictionaries.
        
        Args:
            base_config: Base configuration
            override_config: Configuration to merge (takes precedence)
            
        Returns:
            Merged configuration
        """
        merged = base_config.copy()
        
        for key, value in override_config.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self.merge_configurations(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def load_configuration(
        self, 
        config_file: str = "pipeline_config.yaml",
        environment: Optional[str] = None
    ) -> ConfigurationModel:
        """
        Load and validate pipeline configuration.
        
        Args:
            config_file: Main configuration file name
            environment: Environment-specific configuration to load (e.g., 'dev', 'prod')
            
        Returns:
            Validated configuration model
            
        Raises:
            ConfigurationError: If configuration is invalid or cannot be loaded
        """
        # Load base configuration
        base_config_path = self.config_dir / config_file
        config_data = self.load_yaml_file(base_config_path)
        
        # Load environment-specific overrides if specified
        if environment:
            env_config_path = self.config_dir / "environments" / f"{environment}.yaml"
            if env_config_path.exists():
                env_config = self.load_yaml_file(env_config_path)
                config_data = self.merge_configurations(config_data, env_config)
            else:
                raise ConfigurationError(f"Environment configuration not found: {env_config_path}")
        
        # Substitute environment variables
        try:
            config_data = self.substitute_environment_variables(config_data)
        except ConfigurationError as e:
            raise ConfigurationError(f"Environment variable substitution failed: {e}")
        
        # Validate configuration using Pydantic model
        try:
            return ConfigurationModel(**config_data)
        except ValidationError as e:
            error_msg = "Configuration validation failed:\n"
            for error in e.errors():
                field = " -> ".join(str(x) for x in error['loc'])
                error_msg += f"  {field}: {error['msg']}\n"
            raise ConfigurationError(error_msg.strip())
    
    def validate_configuration_file(self, config_file: str) -> bool:
        """
        Validate a configuration file without loading it fully.
        
        Args:
            config_file: Configuration file to validate
            
        Returns:
            True if configuration is valid
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        try:
            self.load_configuration(config_file)
            return True
        except ConfigurationError:
            raise
    
    def list_environments(self) -> list[str]:
        """
        List available environment configurations.
        
        Returns:
            List of environment names
        """
        env_dir = self.config_dir / "environments"
        if not env_dir.exists():
            return []
        
        environments = []
        for file_path in env_dir.glob("*.yaml"):
            environments.append(file_path.stem)
        
        return sorted(environments)


# Utility functions for common configuration operations
def load_config(
    config_file: str = "pipeline_config.yaml",
    environment: Optional[str] = None,
    config_dir: Optional[Path] = None
) -> ConfigurationModel:
    """
    Convenience function to load pipeline configuration.
    
    Args:
        config_file: Configuration file name
        environment: Environment-specific configuration
        config_dir: Configuration directory path
        
    Returns:
        Validated configuration model
    """
    loader = ConfigLoader(config_dir)
    return loader.load_configuration(config_file, environment)


def validate_config(
    config_file: str = "pipeline_config.yaml",
    config_dir: Optional[Path] = None
) -> bool:
    """
    Convenience function to validate configuration file.
    
    Args:
        config_file: Configuration file name
        config_dir: Configuration directory path
        
    Returns:
        True if configuration is valid
    """
    loader = ConfigLoader(config_dir)
    return loader.validate_configuration_file(config_file)


def get_environment_from_env_var(var_name: str = "PIPELINE_ENV") -> Optional[str]:
    """
    Get environment name from environment variable.
    
    Args:
        var_name: Environment variable name
        
    Returns:
        Environment name or None if not set
    """
    return os.getenv(var_name)