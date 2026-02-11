"""
Provider Status - Manages and validates connectivity to LLM providers.
"""

import logging
from PySide6.QtCore import QObject, Signal, QTimer
from core.settings_manager import SettingsManager
from services.fetch_worker import FetchModelsWorker

class ProviderStatusManager(QObject):
    """
    Central manager to track the connectivity status of LLM providers.
    Uses a Singleton pattern accessible via instance().
    """
    _instance = None
    
    # Signal: provider_name, is_available (bool)
    status_changed = Signal(str, bool)
    
    @classmethod
    def instance(cls):
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = ProviderStatusManager()
        return cls._instance

    def __init__(self):
        """Initialize the manager."""
        super().__init__()
        self.logger = logging.getLogger("ProviderStatus")
        self.settings = SettingsManager()
        
        # Cache for provider status: "ProviderName" -> {"active": True/False, "checking": True/False}
        self.status_cache = {}
        self._active_workers = []

    def get_status(self, provider):
        """
        Returns True if provider is active, False if inactive, or None if unknown/checking.
        Triggers a check if status is unknown.
        
        Args:
            provider (str): Provider name.
            
        Returns:
            bool/None: Status or None if pending.
        """
        if provider not in self.status_cache:
            self.check_provider(provider)
            return None # Status pending
            
        return self.status_cache[provider].get("active")

    def invalidate(self, provider):
        """
        Forces a re-check for the provider.
        
        Args:
            provider (str): Provider name.
        """
        if provider in self.status_cache:
            del self.status_cache[provider]
        self.check_provider(provider)
        
    def check_all(self):
        """Checks all currently configured providers."""
        providers = ["Ollama", "OpenAI", "Gemini", "OpenRouter"]
        for p in providers:
            self.check_provider(p)

    def check_provider(self, provider):
        """
        Initiate a check for a specific provider.
        
        Args:
            provider (str): Provider name.
        """
        # Avoid duplicate checks
        if provider in self.status_cache and self.status_cache[provider].get("checking"):
            return

        # Mark as checking
        self.status_cache[provider] = {"active": self.status_cache.get(provider, {}).get("active", False), "checking": True}
        
        url = ""
        headers = {}
        
        if provider == "Ollama":
            host = self.settings.value("ollama_host", "localhost")
            port = self.settings.value("ollama_port", 11434)
            host = host.replace("http://", "").replace("https://", "").rstrip("/")
            url = f"http://{host}:{port}/api/tags"
        elif provider == "OpenAI":
            key = self.settings.value("openai_key")
            if not key:
                self._update_status(provider, False)
                return
            url = "https://api.openai.com/v1/models"
            headers = {"Authorization": f"Bearer {key}"}
        elif provider == "Gemini":
            key = self.settings.value("gemini_key")
            if not key:
                self._update_status(provider, False)
                return
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
        elif provider == "OpenRouter":
            key = self.settings.value("openrouter_key")
            if not key:
                self._update_status(provider, False)
                return
            url = "https://openrouter.ai/api/v1/models"
            headers = {"Authorization": f"Bearer {key}"}
        else:
            # Unknown provider (e.g. Default implies mapping to one of above, handled by caller)
            return

        # Use FetchModelsWorker for validation
        # We don't need the actual models, just success/fail
        def dummy_parser(data):
            """Parser that ignores data."""
            return []

        worker = FetchModelsWorker(url, headers, dummy_parser)
        self._active_workers.append(worker)
        
        worker.finished.connect(lambda _: self._on_success(provider, worker))
        worker.error.connect(lambda _: self._on_error(provider, worker))
        
        worker.start()

    def _on_success(self, provider, worker):
        """Handle successful check."""
        if worker in self._active_workers:
            self._active_workers.remove(worker)
        self._update_status(provider, True)
        
    def _on_error(self, provider, worker):
        """Handle failed check."""
        if worker in self._active_workers:
            self._active_workers.remove(worker)
        self._update_status(provider, False)

    def _update_status(self, provider, is_active):
        """
        Update internal status and emit signal if changed.
        
        Args:
            provider (str): Provider name.
            is_active (bool): New status.
        """
        old_status = self.status_cache.get(provider, {}).get("active")
        self.status_cache[provider] = {"active": is_active, "checking": False}
        
        # Only emit if changed or was unknown
        if old_status != is_active:
            self.logger.info(f"Provider '{provider}' status changed: {'Online' if is_active else 'Offline'}")
            self.status_changed.emit(provider, is_active)
