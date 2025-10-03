"""
Configuration management for Magic Keys MT5 Trading Manager.
Handles loading, saving, and accessing configuration settings.
"""

import configparser
import os
from typing import Any, Dict, Optional
from src.config.logger import get_logger

logger = get_logger(__name__)


class Settings:
    """Manages application configuration settings."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Singleton pattern to ensure one settings instance."""
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize settings manager."""
        if not Settings._initialized:
            self.config = configparser.ConfigParser()
            self.config_path = self._get_config_path()
            self._load_or_create_config()
            Settings._initialized = True
    
    def _get_config_path(self) -> str:
        """Get the path to the configuration file."""
        # Get the project root directory
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        config_dir = os.path.join(root_dir, 'config')
        
        # Ensure config directory exists
        os.makedirs(config_dir, exist_ok=True)
        
        return os.path.join(config_dir, 'config.ini')
    
    def _load_or_create_config(self):
        """Load existing config or create default one."""
        if os.path.exists(self.config_path):
            try:
                self.config.read(self.config_path, encoding='utf-8')
                logger.info(f"Configuration loaded from: {self.config_path}")
            except Exception as e:
                logger.error(f"Error loading config file: {e}", exc_info=True)
                self._create_default_config()
        else:
            logger.warning("Config file not found. Creating default configuration...")
            self._create_default_config()
    
    def _create_default_config(self):
        """Create default configuration file."""
        # MT5 Settings
        self.config['MT5'] = {
            'login': '',
            'password': '',
            'server': ''
        }
        
        # Trading Settings
        self.config['Trading'] = {
            'default_risk_percent': '1.0',
            'default_pips_distance': '20',
            'default_rr_ratio': '2.0',
            'custom_close_percent': '25',
            'max_slippage': '5',
            'min_lot': '0.01',
            'max_lot': '100.0',
            'lot_step': '0.01'
        }
        
        # Trigger Settings
        self.config['Triggers'] = {
            'auto_be_offset_pips': '5',
            'auto_be_move_to_entry': 'true',
            'partial_tp_enabled': 'true',
            'partial_tp_1_percent': '50',
            'partial_tp_1_default_pips': '15',
            'partial_tp_2_percent': '30',
            'partial_tp_2_default_pips': '30'
        }
        
        # GUI Settings
        self.config['GUI'] = {
            'window_width': '600',
            'window_height': '700',
            'theme': 'dark',
            'font_family': 'Segoe UI',
            'font_size': '10',
            'color_green': '#7FFF00',
            'color_yellow': '#FFD700',
            'color_red': '#FF4444',
            'color_gray': '#CCCCCC',
            'color_background': '#1E1E1E'
        }
        
        # Statistics Settings
        self.config['Statistics'] = {
            'track_stats': 'true',
            'save_stats_on_close': 'true',
            'stats_file': 'data/trading_stats.json'
        }
        
        # Logging Settings
        self.config['Logging'] = {
            'log_level': 'INFO',
            'log_to_console': 'true',
            'log_to_file': 'true',
            'max_log_size_mb': '10',
            'log_backup_count': '5'
        }
        
        # Hotkeys Settings
        self.config['Hotkeys'] = {
            'hotkeys_enabled': 'false'
        }
        
        # Advanced Settings
        self.config['Advanced'] = {
            'check_triggers_interval_ms': '500',
            'connection_timeout_seconds': '10',
            'auto_reconnect': 'true',
            'show_notifications': 'true'
        }
        
        # Save the default config
        self.save()
        logger.info(f"Default configuration created at: {self.config_path}")
    
    def get(self, section: str, key: str, fallback: Any = None) -> str:
        """
        Get a configuration value.
        
        Args:
            section: Configuration section name
            key: Configuration key name
            fallback: Default value if key not found
            
        Returns:
            Configuration value as string
        """
        try:
            return self.config.get(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            logger.warning(f"Config key not found: [{section}]{key}, using fallback: {fallback}")
            return fallback
    
    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        """Get configuration value as integer."""
        try:
            return self.config.getint(section, key, fallback=fallback)
        except ValueError:
            logger.warning(f"Invalid integer value for [{section}]{key}, using fallback: {fallback}")
            return fallback
    
    def get_float(self, section: str, key: str, fallback: float = 0.0) -> float:
        """Get configuration value as float."""
        try:
            return self.config.getfloat(section, key, fallback=fallback)
        except ValueError:
            logger.warning(f"Invalid float value for [{section}]{key}, using fallback: {fallback}")
            return fallback
    
    def get_bool(self, section: str, key: str, fallback: bool = False) -> bool:
        """Get configuration value as boolean."""
        try:
            return self.config.getboolean(section, key, fallback=fallback)
        except ValueError:
            logger.warning(f"Invalid boolean value for [{section}]{key}, using fallback: {fallback}")
            return fallback
    
    def set(self, section: str, key: str, value: Any):
        """
        Set a configuration value.
        
        Args:
            section: Configuration section name
            key: Configuration key name
            value: Value to set
        """
        if not self.config.has_section(section):
            self.config.add_section(section)
        
        self.config.set(section, key, str(value))
        logger.debug(f"Config updated: [{section}]{key} = {value}")
    
    def save(self):
        """Save configuration to file."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                self.config.write(f)
            logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}", exc_info=True)
    
    def reload(self):
        """Reload configuration from file."""
        self._load_or_create_config()
        logger.info("Configuration reloaded")
    
    def get_all_section(self, section: str) -> Dict[str, str]:
        """
        Get all key-value pairs from a section.
        
        Args:
            section: Section name
            
        Returns:
            Dictionary of all settings in the section
        """
        if self.config.has_section(section):
            return dict(self.config.items(section))
        return {}
    
    # Convenience methods for common settings
    
    def get_mt5_credentials(self) -> Dict[str, str]:
        """Get MT5 connection credentials."""
        return {
            'login': self.get('MT5', 'login', ''),
            'password': self.get('MT5', 'password', ''),
            'server': self.get('MT5', 'server', '')
        }
    
    def get_default_risk(self) -> float:
        """Get default risk percentage."""
        return self.get_float('Trading', 'default_risk_percent', 1.0)
    
    def get_default_pips(self) -> int:
        """Get default pips distance."""
        return self.get_int('Trading', 'default_pips_distance', 20)
    
    def get_default_rr(self) -> float:
        """Get default risk:reward ratio."""
        return self.get_float('Trading', 'default_rr_ratio', 2.0)
    
    def get_gui_colors(self) -> Dict[str, str]:
        """Get GUI color scheme."""
        return {
            'green': self.get('GUI', 'color_green', '#7FFF00'),
            'yellow': self.get('GUI', 'color_yellow', '#FFD700'),
            'red': self.get('GUI', 'color_red', '#FF4444'),
            'gray': self.get('GUI', 'color_gray', '#CCCCCC'),
            'background': self.get('GUI', 'color_background', '#1E1E1E')
        }
    
    def get_window_size(self) -> tuple:
        """Get GUI window size."""
        width = self.get_int('GUI', 'window_width', 600)
        height = self.get_int('GUI', 'window_height', 700)
        return (width, height)


# Create global settings instance
settings = Settings()


# Convenience function
def get_settings() -> Settings:
    """
    Get the global settings instance.
    
    Returns:
        Settings: Global settings object
    """
    return settings


# Example usage and testing
if __name__ == "__main__":
    from pprint import pprint
    
    print("Testing Settings Manager\n")
    print("=" * 60)
    
    # Get settings instance
    s = get_settings()
    
    # Test reading settings
    print("\n1. MT5 Credentials:")
    pprint(s.get_mt5_credentials())
    
    print("\n2. Trading Defaults:")
    print(f"   Risk: {s.get_default_risk()}%")
    print(f"   Pips: {s.get_default_pips()}")
    print(f"   R:R: {s.get_default_rr()}")
    
    print("\n3. GUI Colors:")
    pprint(s.get_gui_colors())
    
    print("\n4. Window Size:")
    print(f"   {s.get_window_size()}")
    
    # Test setting and saving
    print("\n5. Testing set and save:")
    s.set('Trading', 'default_risk_percent', '2.5')
    print(f"   New risk: {s.get_default_risk()}%")
    s.save()
    
    print("\n✅ Settings test completed. Check config/config.ini")
