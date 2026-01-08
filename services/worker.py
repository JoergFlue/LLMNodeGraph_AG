
import requests
import json
import os
import logging
from PySide6.QtCore import QThread, Signal
from core.settings_manager import SettingsManager

class LLMWorker(QThread):
    started = Signal()
    chunk_received = Signal(str, str) # node_id, chunk (future use)
    finished = Signal(str, str) # node_id, full_response
    error = Signal(str, str) # node_id, error_message

    def __init__(self, node_id: str, prompt: str, config: dict):
        super().__init__()
        self.node_id = node_id
        self.prompt = prompt
        self.config = config
        self.settings = SettingsManager()
        self.logger = logging.getLogger("LLM.Worker")
        
    def run(self):
        self.started.emit()
        self.logger.info(f"Starting request for Node {self.node_id}")
        try:
            # Determine effective model
            # For now, we trust the node config, but we could allow an override or "auto"
            model = self.config.get("model", "")
            
            # If model is empty or generic, we could fallback to default provider
            # But usually node has a specific model set at creation.
            
            # Provider routing
            if model.startswith("gpt") or model.startswith("o1"):
                 self._call_openai()
            elif model.startswith("gemini"):
                 self._call_gemini()
            else:
                 # Default to Ollama for everything else (llama3, mistral, etc.)
                 self._call_ollama()
                
        except Exception as e:
            self.logger.error(f"Node {self.node_id} failed: {e}")
            self.error.emit(self.node_id, f"Error: {str(e)}")

    def _call_ollama(self):
        host = self.settings.value("ollama_host", "localhost")
        port = self.settings.value("ollama_port", 11434)
        
        # Clean host
        host = host.replace("http://", "").replace("https://", "").rstrip("/")
        base_url = f"http://{host}:{port}"
        url = f"{base_url}/api/generate"
        
        # If node model is set, use it. If not (or generic), fallback to settings default?
        # Node usually has a model.
        model = self.config.get("model", self.settings.value("ollama_model", "llama3"))
        
        payload = {
            "model": model,
            "prompt": self.prompt,
            "stream": False 
        }
        
        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            result = data.get("response", "")
            self.logger.info(f"Ollama response received ({len(result)} chars)")
            self.finished.emit(self.node_id, result)
        except requests.RequestException as e:
            msg = str(e)
            if "404" in msg:
                msg += f"\nCheck if model '{model}' is pulled in Ollama."
            raise Exception(f"Ollama connection failed to {base_url}: {msg}")

    def _call_openai(self):
        api_key = self.settings.value("openai_key")
        if not api_key:
            api_key = os.environ.get("OPENAI_API_KEY")
            
        if not api_key:
            raise Exception("OpenAI API Key not found in Settings or Environment (OPENAI_API_KEY)")
            
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        model = self.config.get("model", self.settings.value("openai_model", "gpt-4o"))
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": self.prompt}],
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            result = data['choices'][0]['message']['content']
            self.logger.info(f"OpenAI response received ({len(result)} chars)")
            self.finished.emit(self.node_id, result)
        except requests.RequestException as e:
             raise Exception(f"OpenAI API failed: {e}")

    def _call_gemini(self):
        api_key = self.settings.value("gemini_key")
        if not api_key:
            raise Exception("Google Gemini API Key not configured in Settings")
            
        model_name = self.config.get("model", self.settings.value("gemini_model", "gemini-1.5-flash"))
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": self.prompt}]
            }]
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            try:
                result = data['candidates'][0]['content']['parts'][0]['text']
                self.logger.info(f"Gemini response received ({len(result)} chars)")
                self.finished.emit(self.node_id, result)
            except (KeyError, IndexError):
                error_msg = json.dumps(data) if data else "Empty response"
                raise Exception(f"Unexpected Gemini response: {error_msg}")
                
        except requests.RequestException as e:
             raise Exception(f"Gemini API failed: {e}")
