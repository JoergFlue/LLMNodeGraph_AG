
import pytest
from unittest.mock import MagicMock, patch
from core.provider_manager import ProviderManager
from core.llm_providers import ProviderFactory, OpenAIStrategy, GeminiStrategy, OllamaStrategy, OpenRouterStrategy

# --- ProviderManager Tests ---

@patch('core.provider_manager.SettingsManager')
def test_resolve_effective_provider_explicit(mock_settings_cls):
    # If provider is explicit, it should return it without checking settings
    assert ProviderManager.resolve_effective_provider("OpenAI", "gpt-4o") == "OpenAI"
    assert ProviderManager.resolve_effective_provider("Gemini", "gemini-1.5") == "Gemini"

@patch('core.provider_manager.SettingsManager')
def test_resolve_effective_provider_heuristic(mock_settings_cls):
    # Mock settings not needed for heuristic if model is provided
    
    # "Default" provider with model prefix
    assert ProviderManager.resolve_effective_provider("Default", "gpt-4o") == "OpenAI"
    assert ProviderManager.resolve_effective_provider(None, "gpt-4o") == "OpenAI"
    
    assert ProviderManager.resolve_effective_provider("Default", "gemini-pro") == "Gemini"
    
    assert ProviderManager.resolve_effective_provider("Default", "llama3") == "Ollama"

@patch('core.provider_manager.SettingsManager')
def test_resolve_effective_provider_fallback(mock_settings_cls):
    # Mock settings
    mock_settings = MagicMock()
    mock_settings_cls.return_value = mock_settings
    mock_settings.value.return_value = "Gemini" # Default Global Provider
    
    # "Default" provider, No model -> fallback to global setting
    assert ProviderManager.resolve_effective_provider("Default", "") == "Gemini"
    mock_settings.value.assert_called_with("default_provider", "Ollama")

@patch('core.provider_manager.SettingsManager')
def test_resolve_display_text(mock_settings_cls):
    # Explicit
    assert ProviderManager.resolve_display_text("OpenAI", "gpt-4") == "OpenAI/gpt-4"
    
    # Default with Model
    assert ProviderManager.resolve_display_text("Default", "gpt-3.5") == "OpenAI/gpt-3.5"
    
    # Default without Model (Global Settings)
    mock_settings = MagicMock()
    mock_settings_cls.return_value = mock_settings
    
    def settings_side_effect(key, default=None):
        if key == "default_provider": return "OpenAI"
        if key == "openai_model": return "gpt-4-turbo"
        return default
    mock_settings.value.side_effect = settings_side_effect
    
    assert ProviderManager.resolve_display_text("Default", "") == "OpenAI/gpt-4-turbo"


# --- ProviderFactory Tests ---

def test_provider_factory_strategies():
    assert isinstance(ProviderFactory.get_strategy("OpenAI"), OpenAIStrategy)
    assert isinstance(ProviderFactory.get_strategy("Gemini"), GeminiStrategy)
    assert isinstance(ProviderFactory.get_strategy("OpenRouter"), OpenRouterStrategy)
    
    # Ollama is default
    assert isinstance(ProviderFactory.get_strategy("Ollama"), OllamaStrategy)
    assert isinstance(ProviderFactory.get_strategy("Unknown"), OllamaStrategy)
