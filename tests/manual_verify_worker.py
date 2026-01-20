
import asyncio
import httpx
from unittest.mock import MagicMock, patch
import sys
import os

# Add parent dir to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.worker import LLMWorker

async def manual_test():
    print("Starting manual test...")
    # Mock settings
    with patch('services.worker.SettingsManager') as mock_settings:
        mock_settings.return_value.value.side_effect = lambda key, default=None: {
            "ollama_host": "localhost",
            "ollama_port": 11434,
            "ollama_model": "llama3"
        }.get(key, default)
        
        worker = LLMWorker("test_node", "Hello", {"provider": "Ollama"})
        
        # Mock httpx.AsyncClient.post
        async def mock_post(*args, **kwargs):
            print("Mock post called")
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"response": "Mocked response"}
            mock_resp.status_code = 200
            mock_resp.raise_for_status = MagicMock()
            return mock_resp

        with patch('httpx.AsyncClient.post', side_effect=mock_post):
            worker.finished = MagicMock()
            print("Running _async_run...")
            await worker._async_run()
            
            try:
                worker.finished.emit.assert_called_with("test_node", "Mocked response")
                print("SUCCESS: Signal emitted correctly")
            except AssertionError:
                print("FAILURE: Signal not emitted correctly")

if __name__ == "__main__":
    asyncio.run(manual_test())
