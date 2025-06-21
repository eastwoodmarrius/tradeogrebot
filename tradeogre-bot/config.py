#!/usr/bin/env python3
"""
Configuration management for TradeOgre Grid Bot
Provides secure configuration loading and validation
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class TradingConfig:
    """Trading configuration parameters"""
    bot_ticker: str = 'AEGS-USDT'
    bot_balance: float = 100.0
    buffer: float = 0.00001
    upper_bound: float = 0.001
    grid_count: int = 10
    pulse_interval: int = 5
    max_position: float = 1000.0
    max_orders_per_side: int = 10
    emergency_stop_price_deviation: float = 0.5
    max_consecutive_failures: int = 5
    max_daily_loss: float = 100.0
    dry_run: bool = True  # Default to paper trading


@dataclass
class SecurityConfig:
    """Security configuration parameters"""
    api_key_file: str = os.path.expanduser('~/.config/tradeogre/api.key')
    log_file: str = os.path.expanduser('~/.config/tradeogre/bot.log')
    max_log_size: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5


class ConfigManager:
    """Manages bot configuration with validation and security"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or os.path.expanduser('~/.config/tradeogre/config.json')
        self.trading_config = TradingConfig()
        self.security_config = SecurityConfig()
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """Setup secure logging configuration"""
        logger = logging.getLogger('tradeogre_bot')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(self.security_config.log_file)
        os.makedirs(log_dir, exist_ok=True)
        
        # File handler with rotation
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            self.security_config.log_file,
            maxBytes=self.security_config.max_log_size,
            backupCount=self.security_config.log_backup_count
        )
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def load_config(self) -> bool:
        """Load configuration from file with validation"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                
                # Update trading config
                if 'trading' in config_data:
                    for key, value in config_data['trading'].items():
                        if hasattr(self.trading_config, key):
                            setattr(self.trading_config, key, value)
                
                # Update security config
                if 'security' in config_data:
                    for key, value in config_data['security'].items():
                        if hasattr(self.security_config, key):
                            setattr(self.security_config, key, value)
                
                self.logger.info(f"Configuration loaded from {self.config_file}")
                return True
            else:
                self.logger.warning(f"Config file not found: {self.config_file}")
                self.save_config()  # Create default config
                return False
                
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            return False
    
    def save_config(self) -> bool:
        """Save current configuration to file"""
        try:
            # Create config directory if it doesn't exist
            config_dir = os.path.dirname(self.config_file)
            os.makedirs(config_dir, exist_ok=True)
            
            config_data = {
                'trading': asdict(self.trading_config),
                'security': asdict(self.security_config)
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            # Set secure permissions
            os.chmod(self.config_file, 0o600)
            
            self.logger.info(f"Configuration saved to {self.config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            return False
    
    def validate_config(self) -> bool:
        """Validate configuration parameters"""
        errors = []
        
        # Validate trading config
        if self.trading_config.bot_balance <= 0:
            errors.append("bot_balance must be positive")
        
        if self.trading_config.buffer <= 0:
            errors.append("buffer must be positive")
        
        if self.trading_config.upper_bound <= 0:
            errors.append("upper_bound must be positive")
        
        if self.trading_config.grid_count < 2:
            errors.append("grid_count must be at least 2")
        
        if self.trading_config.max_position <= 0:
            errors.append("max_position must be positive")
        
        if not self.trading_config.bot_ticker or '-' not in self.trading_config.bot_ticker:
            errors.append("bot_ticker must be in format 'BASE-QUOTE'")
        
        # Validate security config
        if not os.path.exists(os.path.dirname(self.security_config.api_key_file)):
            try:
                os.makedirs(os.path.dirname(self.security_config.api_key_file), exist_ok=True)
            except Exception:
                errors.append(f"Cannot create API key directory: {os.path.dirname(self.security_config.api_key_file)}")
        
        if errors:
            for error in errors:
                self.logger.error(f"Configuration validation error: {error}")
            return False
        
        self.logger.info("Configuration validation passed")
        return True
    
    def get_api_credentials(self) -> tuple[str, str]:
        """Securely load API credentials"""
        try:
            if not os.path.exists(self.security_config.api_key_file):
                raise FileNotFoundError(f"API key file not found: {self.security_config.api_key_file}")
            
            # Check file permissions
            file_stat = os.stat(self.security_config.api_key_file)
            if file_stat.st_mode & 0o077:
                self.logger.warning("API key file has overly permissive permissions")
            
            with open(self.security_config.api_key_file, 'r') as f:
                lines = f.read().strip().split('\n')
                if len(lines) < 2:
                    raise ValueError("API key file must contain key on first line and secret on second line")
                
                api_key = lines[0].strip()
                api_secret = lines[1].strip()
                
                if not api_key or not api_secret:
                    raise ValueError("API key and secret cannot be empty")
                
                return api_key, api_secret
                
        except Exception as e:
            self.logger.error(f"Error loading API credentials: {e}")
            raise
    
    def create_sample_config(self) -> None:
        """Create a sample configuration file"""
        sample_config = {
            "trading": {
                "bot_ticker": "AEGS-USDT",
                "bot_balance": 100.0,
                "buffer": 0.00001,
                "upper_bound": 0.001,
                "grid_count": 10,
                "pulse_interval": 5,
                "max_position": 1000.0,
                "max_orders_per_side": 10,
                "emergency_stop_price_deviation": 0.5,
                "max_consecutive_failures": 5,
                "max_daily_loss": 100.0,
                "dry_run": True
            },
            "security": {
                "api_key_file": "~/.config/tradeogre/api.key",
                "log_file": "~/.config/tradeogre/bot.log",
                "max_log_size": 10485760,
                "log_backup_count": 5
            }
        }
        
        sample_file = self.config_file + '.sample'
        with open(sample_file, 'w') as f:
            json.dump(sample_config, f, indent=2)
        
        print(f"Sample configuration created at: {sample_file}")
        print("Copy this to config.json and modify as needed")


if __name__ == "__main__":
    # Create sample configuration
    config_manager = ConfigManager()
    config_manager.create_sample_config()