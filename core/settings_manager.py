"""
Settings Manager - Handles loading and saving of application settings.
"""

import json
import os
from pathlib import Path
from core.event_bus import EventBus

class SettingsManager:
    """Singleton manager for application settings using JSON storage."""
    _instance = None
    
    def __new__(cls):
        """Ensure singleton instance of the settings manager."""
        if cls._instance is None:
            cls._instance = super(SettingsManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the settings manager."""
        if self._initialized:
            return
            
        self.settings_dir = Path(".usersettings")
        self.settings_file = self.settings_dir / "settings.json"
        self.settings = {}
        
        self.load()
        self._initialized = True

    def load(self):
        """
        Load settings from file.
        """
        if self.settings_file.exists():
            try:
                with open(self.settings_file, "r") as f:
                    self.settings = json.load(f)
            except Exception as e:
                print(f"Error loading settings: {e}")
                self.settings = {}
        else:
            self.settings = {}

    def save(self):
        """
        Save settings to file.
        """
        try:
            self.settings_dir.mkdir(parents=True, exist_ok=True)
            with open(self.settings_file, "w") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def value(self, key, default=None):
        """
        Get a setting value.
        
        Args:
            key (str): Setting key.
            default (Any): Default value.
            
        Returns:
            Any: Setting value.
        """
        return self.settings.get(key, default)

    def setValue(self, key, value):
        """
        Set a setting value.
        
        Args:
            key (str): Setting key.
            value (Any): New value.
        """
        old_value = self.settings.get(key)
        self.settings[key] = value
        self.save()
        
        if old_value != value:
            # Emit signal via EventBus
            try:
                EventBus.instance().settings_changed.emit(key, value)
            except Exception as e:
                print(f"Error emitting settings_changed: {e}")

    def sync(self):
        """Force sync (save) to disk."""
        self.save()

