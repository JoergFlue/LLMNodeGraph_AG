
import httpx
import json
from PySide6.QtCore import QThread, Signal

class FetchModelsWorker(QThread):
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, url, headers=None, parser=None):
        super().__init__()
        self.url = url
        self.headers = headers or {}
        self.parser = parser

    def run(self):
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(self.url, headers=self.headers)
                resp.raise_for_status()
                data = resp.json()
                
                if self.parser:
                    models = self.parser(data)
                else:
                    models = data # fallback
                
                self.finished.emit(models)
        except Exception as e:
            self.error.emit(str(e))
