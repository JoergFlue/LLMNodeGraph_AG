import json
import os
from pathlib import Path

class SettingsManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SettingsManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self.settings_dir = Path(".usersettings")
        self.settings_file = self.settings_dir / "settings.json"
        self.settings = {}
        
        self.load()
        self._initialized = True

    def load(self):
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
        try:
            self.settings_dir.mkdir(parents=True, exist_ok=True)
            with open(self.settings_file, "w") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def value(self, key, default=None):
        return self.settings.get(key, default)

    def setValue(self, key, value):
        self.settings[key] = value
        self.save()

    def sync(self):
        self.save()
