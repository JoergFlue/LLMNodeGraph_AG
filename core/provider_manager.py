"""
ProviderManager - Central logic for resolving LLM providers and models.
"""

from typing import Tuple
from core.settings_manager import SettingsManager

class ProviderManager:
    """
    Manages logic for determining the effective provider and model
    based on node configuration and global settings.
    """
    
    @staticmethod
    def resolve_effective_provider(config_provider: str, config_model: str) -> str:
        """
        Determine the actual provider to use.
        
        Args:
            config_provider: Provider from node config (can be "Default" or None)
            config_model: Model from node config
            
        Returns:
            The effective provider name (e.g., "OpenAI", "Ollama")
        """
        provider = config_provider or "Default"
        
        if provider != "Default":
            return provider
            
        # "Default" resolution logic
        settings = SettingsManager()
        
        if not config_model:
            # excessive fallback: if no model, use global default provider
            return settings.value("default_provider", "Ollama")
            
        # Heuristic based on model name prefix
        if config_model.startswith("gpt") or config_model.startswith("o1"):
            return "OpenAI"
        elif config_model.startswith("gemini"):
            return "Gemini"
        elif config_model.startswith("openrouter"): # explicit prefix sometimes used
             return "OpenRouter"
        else:
            return "Ollama"

    @staticmethod
    def resolve_display_text(config_provider: str, config_model: str) -> str:
        """
        Get the text to display on the node (Provider/Model).
        
        Args:
            config_provider: Provider from node config
            config_model: Model from node config
            
        Returns:
            Formatted string "Provider/Model"
        """
        provider = config_provider or "Default"
        model = config_model or ""
        
        display_provider = provider
        display_model = model
        
        if provider == "Default":
            settings = SettingsManager()
            if not model:
                # No model set on node -> use global default
                display_provider = settings.value("default_provider", "Ollama")
                if display_provider == "OpenAI":
                    display_model = settings.value("openai_model", "gpt-4o")
                elif display_provider == "Gemini":
                    display_model = settings.value("gemini_model", "gemini-1.5-flash")
                elif display_provider == "OpenRouter":
                     display_model = settings.value("openrouter_model", "openai/gpt-3.5-turbo")
                else:
                    display_model = settings.value("ollama_model", "llama3")
            else:
                # Model set, implies provider via heuristic
                display_provider = ProviderManager.resolve_effective_provider("Default", model)
                display_model = model
        
        return f"{display_provider}/{display_model}" if display_model else display_provider
