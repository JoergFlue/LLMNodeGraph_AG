
import httpx
import json
import os
import logging
import asyncio
import time
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
        self.is_cancelled = False
        self._start_time = 0
        self._loop = None
        self._current_task = None

    def cancel(self):
        self.is_cancelled = True
        if self._loop and self._current_task:
            self._loop.call_soon_threadsafe(self._current_task.cancel)
        
    def run(self):
        self._start_time = time.time()
        import uuid
        request_id = str(uuid.uuid4())[:8]
        
        # Create context-aware logger
        extra = {'node_id': f"[{self.node_id}] ", 'request_id': request_id}
        adapter = logging.LoggerAdapter(self.logger, extra)
        
        self.started.emit()
        adapter.info(f"Starting async request (ReqID: {request_id})")
        
        if self.is_cancelled: return

        # Create and run a new event loop in this thread
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        try:
            self._current_task = self._loop.create_task(self._async_run(adapter))
            self._loop.run_until_complete(self._current_task)
            
            duration = time.time() - self._start_time
            adapter.info(f"Task finished in {duration:.2f}s")
            
        except asyncio.CancelledError:
            adapter.info(f"Task was cancelled.")
        except Exception as e:
            adapter.error(f"Task failed: {e}", exc_info=True)
            self.error.emit(self.node_id, f"Error: {str(e)}")
        finally:
            self._loop.close()
            self._loop = None
            self._current_task = None

    async def _async_run(self, logger):
        try:
            # Determine effective model
            model = self.config.get("model", "")
            provider = self.config.get("provider", "Default")
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                # Explicit Provider Override
                if provider == "OpenAI":
                    await self._call_openai(client, logger)
                elif provider == "Gemini":
                    await self._call_gemini(client, logger)
                elif provider == "OpenRouter":
                    await self._call_openrouter(client, logger)
                elif provider == "Ollama":
                    await self._call_ollama(client, logger)
                else:
                    # Fallback to heuristic (Default)
                    if model.startswith("gpt") or model.startswith("o1"):
                         await self._call_openai(client, logger)
                    elif model.startswith("gemini"):
                         await self._call_gemini(client, logger)
                    else:
                         # Default to Ollama for everything else
                         await self._call_ollama(client, logger)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            # Re-raise to be handled in run()
            raise e

    async def _call_ollama(self, client: httpx.AsyncClient, logger):
        host = self.settings.value("ollama_host", "localhost")
        port = self.settings.value("ollama_port", 11434)
        
        # Clean host
        host = host.replace("http://", "").replace("https://", "").rstrip("/")
        base_url = f"http://{host}:{port}"
        url = f"{base_url}/api/generate"
        
        model = self.config.get("model", self.settings.value("ollama_model", "llama3"))
        
        payload = {
            "model": model,
            "prompt": self.prompt,
            "stream": False 
        }
        
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            result = data.get("response", "")
            
            if self.is_cancelled: return
            logger.info(f"Ollama response received ({len(result)} chars)")
            self.finished.emit(self.node_id, result)
        except httpx.HTTPError as e:
            msg = str(e)
            if response is not None and response.status_code == 404:
                msg += f"\nCheck if model '{model}' is pulled in Ollama."
            raise Exception(f"Ollama connection failed to {base_url}: {msg}")

    async def _call_openai(self, client: httpx.AsyncClient, logger):
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
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            result = data['choices'][0]['message']['content']
            
            if self.is_cancelled: return
            logger.info(f"OpenAI response received ({len(result)} chars)")
            self.finished.emit(self.node_id, result)
        except httpx.HTTPError as e:
             raise Exception(f"OpenAI API failed: {e}")

    async def _call_gemini(self, client: httpx.AsyncClient, logger):
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
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            try:
                result = data['candidates'][0]['content']['parts'][0]['text']
                
                if self.is_cancelled: return
                logger.info(f"Gemini response received ({len(result)} chars)")
                self.finished.emit(self.node_id, result)
            except (KeyError, IndexError):
                error_msg = json.dumps(data) if data else "Empty response"
                raise Exception(f"Unexpected Gemini response: {error_msg}")
                
        except httpx.HTTPError as e:
             raise Exception(f"Gemini API failed: {e}")

    async def _call_openrouter(self, client: httpx.AsyncClient, logger):
        api_key = self.settings.value("openrouter_key")
        if not api_key:
            raise Exception("OpenRouter API Key not configured in Settings")
            
        model = self.config.get("model", self.settings.value("openrouter_model", "openai/gpt-3.5-turbo"))
        
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com/JoergFlue/LLMNodeGraph_AG",
            "X-Title": "AntiGravity",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": self.prompt}],
        }
        
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            result = data['choices'][0]['message']['content']
            
            if self.is_cancelled: return
            logger.info(f"OpenRouter response received ({len(result)} chars)")
            self.finished.emit(self.node_id, result)
        except httpx.HTTPError as e:
             raise Exception(f"OpenRouter API failed: {e}")
