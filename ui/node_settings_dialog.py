
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QComboBox, 
                               QDialogButtonBox, QFormLayout, QMessageBox, 
                               QPushButton, QHBoxLayout, QWidget)
from PySide6.QtCore import Qt, Signal
import requests
from core.settings_manager import SettingsManager

class NodeSettingsDialog(QDialog):
    def __init__(self, current_provider="Default", current_model="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Node LLM Settings")
        self.resize(400, 200)
        self.settings = SettingsManager()
        
        self.selected_provider = current_provider
        self.selected_model = current_model
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        # 1. Interface / Provider Selection
        self.combo_provider = QComboBox()
        
        # Build provider list based on config presence
        providers = ["Default"]
        if self.settings.value("ollama_host", "localhost"):
             providers.append("Ollama")
        if self.settings.value("openai_key", ""):
             providers.append("OpenAI")
        if self.settings.value("gemini_key", ""):
             providers.append("Gemini")
        if self.settings.value("openrouter_key", ""):
             providers.append("OpenRouter")
             
        self.combo_provider.addItems(providers)
        
        # Ensure current provider is valid or fallback
        if current_provider in providers:
             self.combo_provider.setCurrentText(current_provider)
        else:
             self.combo_provider.setCurrentText("Default")
             
        self.combo_provider.currentTextChanged.connect(self.on_provider_changed)
        form.addRow("Interface:", self.combo_provider)
        
        # 2. Model Selection
        self.combo_model = QComboBox()
        self.combo_model.setEditable(True)
        self.combo_model.setPlaceholderText("Select or type model...")
        self.combo_model.setEditText(current_model)
        
        # Refresh Button
        self.btn_refresh = QPushButton("⟳")
        self.btn_refresh.setFixedWidth(30)
        self.btn_refresh.setToolTip("Fetch Models for selected interface")
        self.btn_refresh.clicked.connect(self.fetch_models)
        
        h_model = QHBoxLayout()
        h_model.addWidget(self.combo_model)
        h_model.addWidget(self.btn_refresh)
        
        form.addRow("Model:", h_model)
        
        layout.addLayout(form)
        layout.addStretch()
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept_changes)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Initial State
        self.on_provider_changed(current_provider)

    def on_provider_changed(self, text):
        self.selected_provider = text
        if text == "Default":
            self.combo_model.setEnabled(False)
            self.btn_refresh.setEnabled(False)
            self.combo_model.setEditText("")
            self.combo_model.setPlaceholderText("Using Global Default")
        else:
            self.combo_model.setEnabled(True)
            self.btn_refresh.setEnabled(True)
            self.combo_model.setPlaceholderText("Select or type model...")
            
            # Reset model combo on provider change (unless initializing)
            # We check if the text matches because on Init we might set it programmatically
            # But here we want to clear if the USER changed it.
            # Actually simplest is: if self.isVisible(), it's user interaction.
            if self.isVisible():
                self.combo_model.clear()
                self.combo_model.setEditText("")
                # Auto-fetch models
                self.fetch_models(auto=True)

    def fetch_models(self, auto=False):
        provider = self.combo_provider.currentText()
        
        if provider == "Ollama":
            self._fetch_ollama(auto)
        elif provider == "OpenAI":
            self._fetch_openai(auto)
        elif provider == "Gemini":
            self._fetch_gemini(auto)
        elif provider == "OpenRouter":
            self._fetch_openrouter(auto)

    def _fetch_ollama(self, auto=False):
        host = self.settings.value("ollama_host", "localhost")
        port = self.settings.value("ollama_port", 11434)
        
        host = host.replace("http://", "").replace("https://", "").rstrip("/")
        base_url = f"http://{host}:{port}"
        
        try:
            resp = requests.get(f"{base_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                models = [m['name'] for m in data.get('models', [])]
                self._update_model_list(models, auto)
            elif not auto:
                QMessageBox.warning(self, "Error", f"Status {resp.status_code}: {resp.text}")
        except Exception as e:
            if not auto: QMessageBox.critical(self, "Error", f"Fetch failed: {e}")

    def _fetch_openai(self, auto=False):
        key = self.settings.value("openai_key")
        if not key:
            if not auto: QMessageBox.warning(self, "Missing Key", "Configure OpenAI API Key in Global Settings first.")
            return

        try:
            headers = {"Authorization": f"Bearer {key}"}
            resp = requests.get("https://api.openai.com/v1/models", headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                models = [m['id'] for m in data.get('data', []) if 'gpt' in m['id']]
                models.sort()
                self._update_model_list(models, auto)
            elif not auto:
                 QMessageBox.warning(self, "Error", f"Status {resp.status_code}")
        except Exception as e:
             if not auto: QMessageBox.critical(self, "Error", f"Fetch failed: {e}")

    def _fetch_gemini(self, auto=False):
        key = self.settings.value("gemini_key")
        if not key:
            if not auto: QMessageBox.warning(self, "Missing Key", "Configure Gemini API Key in Global Settings first.")
            return

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                models = [m['name'].replace("models/", "") for m in data.get('models', []) if 'gemini' in m['name']]
                models.sort()
                self._update_model_list(models, auto)
            elif not auto:
                 QMessageBox.warning(self, "Error", f"Status {resp.status_code}")
        except Exception as e:
             if not auto: QMessageBox.critical(self, "Error", f"Fetch failed: {e}")

    def _fetch_openrouter(self, auto=False):
        key = self.settings.value("openrouter_key")
        if not key:
            if not auto: QMessageBox.warning(self, "Missing Key", "Configure OpenRouter API Key in Global Settings first.")
            return

        try:
            url = "https://openrouter.ai/api/v1/models"
            headers = {"Authorization": f"Bearer {key}"}
            resp = requests.get(url, headers=headers, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                models = [m['id'] for m in data.get('data', [])]
                models.sort()
                self._update_model_list(models, auto)
            elif not auto:
                 QMessageBox.warning(self, "Error", f"Status {resp.status_code}")
        except Exception as e:
             if not auto: QMessageBox.critical(self, "Error", f"Fetch failed: {e}")

    def _update_model_list(self, models, auto=False):
        current = self.combo_model.currentText()
        self.combo_model.clear()
        self.combo_model.addItems(models)
        self.combo_model.setEditText(current)
        if not auto: QMessageBox.information(self, "Success", f"Fetched {len(models)} models.")

    def accept_changes(self):
        self.selected_provider = self.combo_provider.currentText()
        self.selected_model = self.combo_model.currentText()
        self.accept()
