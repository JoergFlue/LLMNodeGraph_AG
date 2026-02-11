"""
LLM Providers - Strategy Pattern implementation for LLM generation.
"""

import os
import json
import logging
import httpx
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from core.settings_manager import SettingsManager

class LLMStrategy(ABC):
    """Abstract base class for LLM generation strategies."""
    
    @abstractmethod
    async def generate(self, 
                       client: httpx.AsyncClient, 
                       prompt: str, 
                       config: Dict[str, Any], 
                       settings: SettingsManager, 
                       logger: logging.Logger) -> str:
        """
        Generate text from the LLM.
        
        Args:
            client: Async HTTP client
            prompt: Input text
            config: Node configuration
            settings: Application settings
            logger: Context-aware logger
            
        Returns:
            Generated text response
        """
        pass

class OpenAIStrategy(LLMStrategy):
    """Strategy for generating text using the OpenAI API."""
    async def generate(self, client: httpx.AsyncClient, prompt: str, config: Dict[str, Any], settings: SettingsManager, logger: logging.Logger) -> str:
        """
        Generate text using OpenAI API.
        
        Args:
            client (httpx.AsyncClient): Async HTTP client.
            prompt (str): Prompt text.
            config (Dict): Node config.
            settings (SettingsManager): App settings.
            logger (logging.Logger): Logger.
            
        Returns:
            str: Generated text.
        """
        api_key = settings.value("openai_key")
        if not api_key:
            api_key = os.environ.get("OPENAI_API_KEY")
            
        if not api_key:
            raise Exception("OpenAI API Key not found in Settings or Environment (OPENAI_API_KEY)")
            
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        model = config.get("model", settings.value("openai_model", "gpt-4o"))
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        }
        
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            result = data['choices'][0]['message']['content']
            
            logger.info(f"OpenAI response received ({len(result)} chars)")
            return result
        except httpx.HTTPError as e:
             raise Exception(f"OpenAI API failed: {e}")

class GeminiStrategy(LLMStrategy):
    """Strategy for generating text using the Google Gemini API."""
    async def generate(self, client: httpx.AsyncClient, prompt: str, config: Dict[str, Any], settings: SettingsManager, logger: logging.Logger) -> str:
        """
        Generate text using Google Gemini API.
        
        Args:
           client (httpx.AsyncClient): Async HTTP client.
           prompt (str): Prompt text.
           config (Dict): Node config.
           settings (SettingsManager): App settings.
           logger (logging.Logger): Logger.
           
        Returns:
           str: Generated text.
        """
        api_key = settings.value("gemini_key")
        if not api_key:
            raise Exception("Google Gemini API Key not configured in Settings")
            
        model_name = config.get("model", settings.value("gemini_model", "gemini-1.5-flash"))
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            try:
                result = data['candidates'][0]['content']['parts'][0]['text']
                logger.info(f"Gemini response received ({len(result)} chars)")
                return result
            except (KeyError, IndexError):
                error_msg = json.dumps(data) if data else "Empty response"
                raise Exception(f"Unexpected Gemini response: {error_msg}")
                
        except httpx.HTTPError as e:
             raise Exception(f"Gemini API failed: {e}")

class OllamaStrategy(LLMStrategy):
    """Strategy for generating text using a local Ollama instance."""
    async def generate(self, client: httpx.AsyncClient, prompt: str, config: Dict[str, Any], settings: SettingsManager, logger: logging.Logger) -> str:
        """
        Generate text using Ollama (local).
        
        Args:
           client (httpx.AsyncClient): Async HTTP client.
           prompt (str): Prompt text.
           config (Dict): Node config.
           settings (SettingsManager): App settings.
           logger (logging.Logger): Logger.
           
        Returns:
           str: Generated text.
        """
        host = settings.value("ollama_host", "localhost")
        port = settings.value("ollama_port", 11434)
        
        # Clean host
        host = host.replace("http://", "").replace("https://", "").rstrip("/")
        base_url = f"http://{host}:{port}"
        url = f"{base_url}/api/generate"
        
        model = config.get("model", settings.value("ollama_model", "llama3"))
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False 
        }
        
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            result = data.get("response", "")
            
            logger.info(f"Ollama response received ({len(result)} chars)")
            return result
        except httpx.HTTPError as e:
            msg = str(e)
            if 'response' in locals() and response is not None and response.status_code == 404:
                msg += f"\nCheck if model '{model}' is pulled in Ollama."
            raise Exception(f"Ollama connection failed to {base_url}: {msg}")

class OpenRouterStrategy(LLMStrategy):
    """Strategy for generating text using the OpenRouter API."""
    async def generate(self, client: httpx.AsyncClient, prompt: str, config: Dict[str, Any], settings: SettingsManager, logger: logging.Logger) -> str:
        """
        Generate text using OpenRouter API.
        
        Args:
           client (httpx.AsyncClient): Async HTTP client.
           prompt (str): Prompt text.
           config (Dict): Node config.
           settings (SettingsManager): App settings.
           logger (logging.Logger): Logger.
           
        Returns:
           str: Generated text.
        """
        api_key = settings.value("openrouter_key")
        if not api_key:
            raise Exception("OpenRouter API Key not configured in Settings")
            
        model = config.get("model", settings.value("openrouter_model", "openai/gpt-3.5-turbo"))
        
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com/JoergFlue/LLMNodeGraph_AG",
            "X-Title": "AntiGravity",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        }
        
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            result = data['choices'][0]['message']['content']
            
            logger.info(f"OpenRouter response received ({len(result)} chars)")
            return result
        except httpx.HTTPError as e:
             raise Exception(f"OpenRouter API failed: {e}")

class ProviderFactory:
    """Factory to create the appropriate LLM strategy."""
    
    _strategies = {
        "OpenAI": OpenAIStrategy(),
        "Gemini": GeminiStrategy(),
        "Ollama": OllamaStrategy(),
        "OpenRouter": OpenRouterStrategy()
    }
    
    @staticmethod
    def get_strategy(provider_name: str) -> LLMStrategy:
        """
        Get the strategy for the given provider.
        Defaults to OllamaStrategy if provider not found.
        """
        return ProviderFactory._strategies.get(provider_name, ProviderFactory._strategies["Ollama"])
