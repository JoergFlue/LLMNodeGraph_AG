"""
EventBus - Centralized signal hub for the application.
"""

from PySide6.QtCore import QObject, Signal

class EventBus(QObject):
    """
    Central event bus for application-wide signals.
    Implements a Singleton pattern.
    """
    
    # --- Signals ---
    
    # Settings
    settings_changed = Signal(str, object)  # key, new_value
    
    # Theme/UI
    theme_changed = Signal(str)             # theme_name
    
    # Providers
    provider_status_updated = Signal(str, bool) # provider, is_active
    
    # --- Singleton ---
    
    _instance = None
    
    @classmethod
    def instance(cls):
        """
        Get the singleton instance of the EventBus.
        
        Returns:
            EventBus: The singleton instance.
        """
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        """Initialize the EventBus."""
        if EventBus._instance:
            raise Exception("EventBus is a singleton! Use EventBus.instance()")
        super().__init__()
