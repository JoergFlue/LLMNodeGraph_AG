
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
            from core.provider_manager import ProviderManager
            from core.llm_providers import ProviderFactory
            
            # Determine effective provider using centralized logic
            config_provider = self.config.get("provider")
            config_model = self.config.get("model")
            
            effective_provider = ProviderManager.resolve_effective_provider(config_provider, config_model)
            logger.info(f"Resolved provider: {effective_provider}")
            
            # Get Strategy
            strategy = ProviderFactory.get_strategy(effective_provider)
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                result = await strategy.generate(client, self.prompt, self.config, self.settings, logger)
                
                if self.is_cancelled: return
                self.finished.emit(self.node_id, result)

        except asyncio.CancelledError:
            raise
        except Exception as e:
            # Re-raise to be handled in run()
            raise e
