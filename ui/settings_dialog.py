
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                               QDialogButtonBox, QFormLayout, QGroupBox, 
                               QComboBox, QTabWidget, QWidget, QSpinBox,
                               QPushButton, QHBoxLayout, QMessageBox, QToolButton)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from core.settings_manager import SettingsManager
from services.fetch_worker import FetchModelsWorker
from .theme import Sizing
import os

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(700, 550)
        self.settings = SettingsManager()
        self._active_workers = []
        
        layout = QVBoxLayout(self)
        
        # --- 1. General / Defaults ---
        box_general = QGroupBox("General Defaults")
        layout_general = QFormLayout()
        
        self.combo_provider = QComboBox()
        self.combo_provider.addItems(["Ollama", "OpenAI", "Gemini", "OpenRouter"])
        layout_general.addRow("Default Provider:", self.combo_provider)
        
        self.edit_token_limit = QLineEdit()
        self.edit_token_limit.setPlaceholderText("16383")
        layout_general.addRow("Global Token Limit:", self.edit_token_limit)
        
        self.spin_undo_stack = QSpinBox()
        self.spin_undo_stack.setRange(10, 200)
        self.spin_undo_stack.setValue(50)
        layout_general.addRow("Undo Stack Size:", self.spin_undo_stack)
        
        box_general.setLayout(layout_general)
        layout.addWidget(box_general)
        
        # --- 2. Provider Configs (Tabs) ---
        self.tabs = QTabWidget()
        
        # -- Ollama Tab --
        self.tabs.addTab(self._create_ollama_tab(), "Ollama")
        
        # -- OpenAI Tab --
        self.tabs.addTab(self._create_openai_tab(), "OpenAI")
        
        # -- Gemini Tab --
        self.tabs.addTab(self._create_gemini_tab(), "Gemini")

        # -- OpenRouter Tab --
        self.tabs.addTab(self._create_openrouter_tab(), "OpenRouter")
        
        layout.addWidget(self.tabs)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply)
        buttons.accepted.connect(self.accept_settings)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.Apply).clicked.connect(self.apply_settings)
        layout.addWidget(buttons)
        
        self.load_settings()

    def _create_ollama_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        form = QFormLayout()
        
        self.edit_ollama_host = QLineEdit()
        self.edit_ollama_host.setPlaceholderText("localhost")
        self.spin_ollama_port = QSpinBox()
        self.spin_ollama_port.setRange(1, 65535)
        self.spin_ollama_port.setValue(11434)
        
        # Model Selection with Refresh
        self.combo_ollama_model = QComboBox()
        self.combo_ollama_model.setEditable(True)
        self.combo_ollama_model.setPlaceholderText("Select or type model...")
        self.combo_ollama_model.currentTextChanged.connect(self._update_ollama_btn_state)
        
        btn_refresh = QToolButton()
        btn_refresh.setText("⟳") # Refresh symbol
        btn_refresh.setToolTip("Fetch Models")
        btn_refresh.clicked.connect(self.fetch_ollama_models)
        
        h_model = QHBoxLayout()
        h_model.addWidget(self.combo_ollama_model)
        h_model.addWidget(btn_refresh)
        
        form.addRow("Host:", self.edit_ollama_host)
        form.addRow("Port:", self.spin_ollama_port)
        form.addRow("Default Model:", h_model)
        layout.addLayout(form)
        
        self.btn_test_ollama = QPushButton("No valid connection")
        self.btn_test_ollama.setEnabled(False)
        self.btn_test_ollama.clicked.connect(self.test_ollama)
        layout.addWidget(self.btn_test_ollama)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget

    def _create_openai_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        form = QFormLayout()
        
        self.edit_openai_key = QLineEdit()
        self.edit_openai_key.setEchoMode(QLineEdit.Password)
        
        self.combo_openai_model = QComboBox()
        self.combo_openai_model.setEditable(True)
        self.combo_openai_model.setPlaceholderText("Select or type model...")
        self.combo_openai_model.currentTextChanged.connect(self._update_openai_btn_state)
        
        btn_refresh = QToolButton()
        btn_refresh.setText("⟳")
        btn_refresh.setToolTip("Fetch Models")
        btn_refresh.clicked.connect(self.fetch_openai_models)
        
        h_model = QHBoxLayout()
        h_model.addWidget(self.combo_openai_model)
        h_model.addWidget(btn_refresh)
        
        form.addRow("API Key:", self.edit_openai_key)
        form.addRow("Default Model:", h_model)
        layout.addLayout(form)
        
        self.btn_test_openai = QPushButton("No valid connection")
        self.btn_test_openai.setEnabled(False)
        self.btn_test_openai.clicked.connect(self.test_openai)
        layout.addWidget(self.btn_test_openai)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget

    def _create_gemini_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        form = QFormLayout()
        
        self.edit_gemini_key = QLineEdit()
        self.edit_gemini_key.setEchoMode(QLineEdit.Password)
        
        self.combo_gemini_model = QComboBox()
        self.combo_gemini_model.setEditable(True)
        self.combo_gemini_model.setPlaceholderText("Select or type model...")
        self.combo_gemini_model.currentTextChanged.connect(self._update_gemini_btn_state)
        
        btn_refresh = QToolButton()
        btn_refresh.setText("⟳")
        btn_refresh.setToolTip("Fetch Models")
        btn_refresh.clicked.connect(self.fetch_gemini_models)
        
        h_model = QHBoxLayout()
        h_model.addWidget(self.combo_gemini_model)
        h_model.addWidget(btn_refresh)
        
        form.addRow("API Key:", self.edit_gemini_key)
        form.addRow("Default Model:", h_model)
        layout.addLayout(form)
        
        self.btn_test_gemini = QPushButton("No valid connection")
        self.btn_test_gemini.setEnabled(False)
        self.btn_test_gemini.clicked.connect(self.test_gemini)
        layout.addWidget(self.btn_test_gemini)
        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def _create_openrouter_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        form = QFormLayout()
        
        self.edit_openrouter_key = QLineEdit()
        self.edit_openrouter_key.setEchoMode(QLineEdit.Password)
        
        self.combo_openrouter_model = QComboBox()
        self.combo_openrouter_model.setEditable(True)
        self.combo_openrouter_model.setPlaceholderText("Select or type model...")
        self.combo_openrouter_model.currentTextChanged.connect(self._update_openrouter_btn_state)
        
        btn_refresh = QToolButton()
        btn_refresh.setText("⟳")
        btn_refresh.setToolTip("Fetch Models")
        btn_refresh.clicked.connect(self.fetch_openrouter_models)
        
        h_model = QHBoxLayout()
        h_model.addWidget(self.combo_openrouter_model)
        h_model.addWidget(btn_refresh)
        
        form.addRow("API Key:", self.edit_openrouter_key)
        form.addRow("Default Model:", h_model)
        layout.addLayout(form)
        
        self.btn_test_openrouter = QPushButton("No valid connection")
        self.btn_test_openrouter.setEnabled(False)
        self.btn_test_openrouter.clicked.connect(self.test_openrouter)
        layout.addWidget(self.btn_test_openrouter)
        layout.addStretch()

        widget.setLayout(layout)
        return widget

    # --- Loading & Saving ---
    def load_settings(self):
        self.combo_provider.setCurrentText(self.settings.value("default_provider", "Ollama"))
        self.edit_token_limit.setText(str(self.settings.value("global_token_limit", 16383)))
        self.spin_undo_stack.setValue(int(self.settings.value("undo_stack_size", 50)))
        
        # Ollama
        self.edit_ollama_host.setText(self.settings.value("ollama_host", "localhost"))
        self.spin_ollama_port.setValue(int(self.settings.value("ollama_port", 11434)))
        self.combo_ollama_model.setEditText(self.settings.value("ollama_model", ""))
        
        # OpenAI
        self.edit_openai_key.setText(self.settings.value("openai_key", ""))
        self.combo_openai_model.setEditText(self.settings.value("openai_model", ""))
        
        # Gemini
        self.edit_gemini_key.setText(self.settings.value("gemini_key", ""))
        self.combo_gemini_model.setEditText(self.settings.value("gemini_model", ""))

        # OpenRouter
        self.edit_openrouter_key.setText(self.settings.value("openrouter_key", ""))
        self.combo_openrouter_model.setEditText(self.settings.value("openrouter_model", ""))
        
        # Check if we can enable buttons based on loaded settings
        self._update_ollama_btn_state()
        self._update_openai_btn_state()
        self._update_gemini_btn_state()
        self._update_openrouter_btn_state()
        
        # Auto-fetch models on load (background)
        self.fetch_ollama_models(auto=True)
        self.fetch_openai_models(auto=True)
        self.fetch_gemini_models(auto=True)
        self.fetch_openrouter_models(auto=True)

    def save_to_disk(self):
        self.settings.setValue("default_provider", self.combo_provider.currentText())
        self.settings.setValue("global_token_limit", self.edit_token_limit.text())
        self.settings.setValue("undo_stack_size", self.spin_undo_stack.value())
        
        self.settings.setValue("ollama_host", self.edit_ollama_host.text())
        self.settings.setValue("ollama_port", self.spin_ollama_port.value())
        self.settings.setValue("ollama_model", self.combo_ollama_model.currentText())
        
        self.settings.setValue("openai_key", self.edit_openai_key.text())
        self.settings.setValue("openai_model", self.combo_openai_model.currentText())
        
        self.settings.setValue("gemini_key", self.edit_gemini_key.text())
        self.settings.setValue("gemini_model", self.combo_gemini_model.currentText())

        self.settings.setValue("openrouter_key", self.edit_openrouter_key.text())
        self.settings.setValue("openrouter_model", self.combo_openrouter_model.currentText())
        
        self.settings.sync()

    def apply_settings(self):
        self.save_to_disk()

    def accept_settings(self):
        self.save_to_disk()
        self.accept()

    # --- UI State Logic ---
    def _update_ollama_btn_state(self):
        if self.combo_ollama_model.currentText().strip():
            self.btn_test_ollama.setEnabled(True)
            self.btn_test_ollama.setText("Test Connection (Ollama)")
        else:
            self.btn_test_ollama.setEnabled(False)
            self.btn_test_ollama.setText("No valid connection")

    def _update_openai_btn_state(self):
        if self.combo_openai_model.currentText().strip() and self.edit_openai_key.text().strip():
            self.btn_test_openai.setEnabled(True)
            self.btn_test_openai.setText("Test Connection (OpenAI)")
        else:
            self.btn_test_openai.setEnabled(False)
            self.btn_test_openai.setText("No valid connection")

    def _update_gemini_btn_state(self):
        if self.combo_gemini_model.currentText().strip() and self.edit_gemini_key.text().strip():
            self.btn_test_gemini.setEnabled(True)
            self.btn_test_gemini.setText("Test Connection (Gemini)")
        else:
            self.btn_test_gemini.setEnabled(False)
            self.btn_test_gemini.setText("No valid connection")

    def _update_openrouter_btn_state(self):
        if self.combo_openrouter_model.currentText().strip() and self.edit_openrouter_key.text().strip():
            self.btn_test_openrouter.setEnabled(True)
            self.btn_test_openrouter.setText("Test Connection (OpenRouter)")
        else:
            self.btn_test_openrouter.setEnabled(False)
            self.btn_test_openrouter.setText("No valid connection")


    # --- Fetching Logic ---
    def fetch_ollama_models(self, auto=False):
        host = self.edit_ollama_host.text().replace("http://", "").replace("https://", "").rstrip("/")
        port = self.spin_ollama_port.value()
        base_url = f"http://{host}:{port}"
        url = f"{base_url}/api/tags"
        
        def parser(data):
            return [m['name'] for m in data.get('models', [])]
        
        self._start_fetch_worker(url, {}, parser, self.combo_ollama_model, auto)

    def fetch_openai_models(self, auto=False):
        key = self.edit_openai_key.text()
        if not key:
            if not auto: QMessageBox.warning(self, "Missing Key", "Enter API Key first.")
            return
            
        url = "https://api.openai.com/v1/models"
        headers = {"Authorization": f"Bearer {key}"}
        
        def parser(data):
            models = [m['id'] for m in data.get('data', []) if 'gpt' in m['id']]
            models.sort()
            return models
        
        self._start_fetch_worker(url, headers, parser, self.combo_openai_model, auto)

    def fetch_gemini_models(self, auto=False):
        key = self.edit_gemini_key.text()
        if not key:
            if not auto: QMessageBox.warning(self, "Missing Key", "Enter API Key first.")
            return

        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
        
        def parser(data):
            models = [m['name'].replace("models/", "") for m in data.get('models', []) if 'gemini' in m['name']]
            models.sort()
            return models
        
        self._start_fetch_worker(url, {}, parser, self.combo_gemini_model, auto)

    def fetch_openrouter_models(self, auto=False):
        key = self.edit_openrouter_key.text()
        if not key:
            if not auto: QMessageBox.warning(self, "Missing Key", "Enter API Key first.")
            return

        url = "https://openrouter.ai/api/v1/models"
        headers = {"Authorization": f"Bearer {key}"}
        
        def parser(data):
            models = [m['id'] for m in data.get('data', [])]
            models.sort()
            return models
        
        self._start_fetch_worker(url, headers, parser, self.combo_openrouter_model, auto)

    def _start_fetch_worker(self, url, headers, parser, combo, auto=False):
        worker = FetchModelsWorker(url, headers, parser)
        self._active_workers.append(worker)
        
        worker.finished.connect(lambda models: self._on_fetch_success(models, combo, auto))
        worker.error.connect(lambda err: self._on_fetch_error(err, auto))
        
        # Cleanup when done
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        worker.error.connect(lambda: self._cleanup_worker(worker))
        
        worker.start()
        # Visual feedback
        if not auto:
            self.setCursor(Qt.WaitCursor)

    def _cleanup_worker(self, worker):
        if worker in self._active_workers:
            self._active_workers.remove(worker)
            worker.deleteLater()

    def _on_fetch_success(self, models, combo, auto=False):
        if not auto:
            self.unsetCursor()
        current = combo.currentText()
        combo.clear()
        combo.addItems(models)
        combo.setEditText(current)
        if not auto:
            QMessageBox.information(self, "Success", f"Fetched {len(models)} models.")

    def _on_fetch_error(self, error_msg, auto=False):
        if not auto:
            self.unsetCursor()
            QMessageBox.critical(self, "Error", f"Fetch failed: {error_msg}")

    # --- Test Functions (Simple Reachability + Model check?) ---
    def test_ollama(self):
        self.fetch_ollama_models() # Reuse fetch as connection test implies ability to fetch
        # Or checking specific model?
        # User said: "Testing button will only work when ... model list has been pulled"
        # So we can assume "Test Connection" here means "Verify Model is Usable", but
        # simple fetch is a strong enough signal for "Connection OK".

    def test_openai(self):
        # We can try a small completion or just list models
        self.fetch_openai_models()

    def test_gemini(self):
        self.fetch_gemini_models()

    def test_openrouter(self):
        self.fetch_openrouter_models()
