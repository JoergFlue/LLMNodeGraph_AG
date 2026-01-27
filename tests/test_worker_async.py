
import pytest
import asyncio
import httpx
from unittest.mock import MagicMock, patch
from services.worker import LLMWorker

@pytest.mark.asyncio
async def test_worker_async_logic():
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
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"response": "Mocked response"}
            mock_resp.status_code = 200
            mock_resp.raise_for_status = MagicMock()
            return mock_resp

        with patch('httpx.AsyncClient.post', side_effect=mock_post):
            # Test the async run method directly
            # We mock AsyncClient itself to control its lifecycle
            with patch('httpx.AsyncClient.__aenter__', return_value=MagicMock(post=mock_post)):
                # We need to mock finished.emit because signals need a QEventLoop 
                # or we can just check if it was called
                worker.finished = MagicMock()
                mock_logger = MagicMock()
                await worker._async_run(mock_logger)
                
                worker.finished.emit.assert_called_with("test_node", "Mocked response")

if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__]))
