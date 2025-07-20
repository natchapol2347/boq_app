#!/usr/bin/env python3
"""
Configuration Manager for BOQ Processor using Pydantic models.
Manages sheet processor configurations including column mappings and header rows.
"""

import json
import os
from typing import Optional
from pathlib import Path
import logging
from models.config_models import (
    ProcessorConfigs,
    ProcessorType,
    ConfigUpdateRequest,
    InteriorProcessorConfig,
    SystemProcessorConfig
)


class ConfigManager:
    """Manages configuration for sheet processors using Pydantic models"""
    
    def __init__(self, config_file_path: Optional[str] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Default config file location
        if config_file_path is None:
            self.config_dir = Path.home() / 'AppData' / 'Roaming' / 'BOQProcessor'
            os.makedirs(self.config_dir, exist_ok=True)
            self.config_file = self.config_dir / 'processor_config.json'
        else:
            self.config_file = Path(config_file_path)
            
        self.config = self._load_config()
    
    def _load_config(self) -> ProcessorConfigs:
        """Load configuration from file, create default if doesn't exist"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                config = ProcessorConfigs(**config_data)
                self.logger.info(f"Loaded configuration from {self.config_file}")
                return config
        except Exception as e:
            self.logger.error(f"Error loading config file: {e}")
        
        # Return default config and save it
        default_config = ProcessorConfigs.get_default_config()
        self._save_config(default_config)
        self.logger.info("Created default configuration")
        return default_config
    
    def _save_config(self, config: ProcessorConfigs) -> None:
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config.model_dump(), f, indent=2, ensure_ascii=False)
            self.logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            self.logger.error(f"Error saving config file: {e}")
            raise
    
    def get_processor_config(self, processor_name: ProcessorType) -> Optional[InteriorProcessorConfig | SystemProcessorConfig]:
        """Get configuration for a specific processor"""
        try:
            return getattr(self.config, processor_name.value)
        except AttributeError:
            self.logger.error(f"Processor '{processor_name}' not found")
            return None
    
    def get_all_configs(self) -> ProcessorConfigs:
        """Get all processor configurations"""
        return self.config
    
    def update_config(self, update_request: ConfigUpdateRequest) -> bool:
        """Update configuration based on request"""
        try:
            processor_name = update_request.processor_name.value
            current_config = getattr(self.config, processor_name)
            
            # Update header row if provided
            if update_request.header_row is not None:
                current_config.header_row = update_request.header_row
                self.logger.info(f"Updated header_row for {processor_name} to {update_request.header_row}")
            
            # Update column mapping if provided
            if update_request.column_mapping is not None:
                # Update the column mapping fields
                for field, value in update_request.column_mapping.items():
                    if hasattr(current_config.column_mapping, field):
                        setattr(current_config.column_mapping, field, value)
                        self.logger.info(f"Updated {field} column for {processor_name} to {value}")
            
            # Save the updated configuration
            self._save_config(self.config)
            self.logger.info(f"Configuration updated successfully for {processor_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating config: {e}")
            return False
    
    def update_header_row(self, processor_name: ProcessorType, header_row: int) -> bool:
        """Update header row for a specific processor"""
        try:
            current_config = getattr(self.config, processor_name.value)
            current_config.header_row = header_row
            self._save_config(self.config)
            
            self.logger.info(f"Updated header row for {processor_name.value} to {header_row}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating header row for {processor_name}: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """Reset configuration to defaults"""
        try:
            self.config = ProcessorConfigs.get_default_config()
            self._save_config(self.config)
            self.logger.info("Configuration reset to defaults")
            return True
        except Exception as e:
            self.logger.error(f"Error resetting config to defaults: {e}")
            return False
    
    def get_config_summary(self) -> dict:
        """Get a summary of current configuration for display"""
        try:
            summary = {}
            for processor_type in ProcessorType:
                config = getattr(self.config, processor_type.value)
                summary[processor_type.value] = {
                    "sheet_pattern": config.sheet_pattern,
                    "header_row": config.header_row,
                    "table_name": config.table_name,
                    "column_mapping": config.column_mapping.model_dump()
                }
            return summary
        except Exception as e:
            self.logger.error(f"Error getting config summary: {e}")
            return {}