# Project Structure

## Directory Organization

```
AntiGravity/
├── core/                    # Core logic and data models
├── services/               # Background services and workers  
├── ui/                     # User interface components
├── tests/                  # Test suite
├── .kiro/                  # Kiro configuration
├── .usersettings/          # User configuration storage
└── main.py                 # Application entry point
```

## Core Modules (`core/`)
- **`node.py`**: Data models (Node, Link, NodeConfig) with serialization
- **`graph.py`**: Graph state management, validation, merging logic
- **`assembler.py`**: Context assembly engine for LLM interactions
- **`command_manager.py`**: Undo/redo system using command pattern
- **`settings_manager.py`**: Persistent configuration management
- **`logging_setup.py`**: Multi-level logging configuration

## Services (`services/`)
- **`worker.py`**: Async LLM integration for all providers
- **`llm_queue_manager.py`**: Task queuing and execution management
- **`fetch_worker.py`**: Background model discovery workers

## UI Components (`ui/`)
- **`main_window.py`**: Application orchestration and menu system
- **`editor_tab.py`**: Individual graph editor with full feature set
- **`canvas.py`**: Graphics scene with pan/zoom and interactions
- **`node_item.py`**: Visual node representation with resizing
- **`settings_dialog.py`**: Multi-tab configuration interface
- **`theme.py`**: Centralized styling and color schemes
- **`wire_item.py`**: Bezier curve connection rendering

## Key Design Patterns
- **Command Pattern**: Complete undo/redo for all operations
- **Observer Pattern**: Signal/slot architecture for loose coupling
- **MVC Architecture**: Clear separation of data, logic, and presentation
- **Factory Pattern**: Dynamic component creation
- **Strategy Pattern**: Pluggable LLM provider system

## File Conventions
- **Graph Files**: JSON format with `.json` extension
- **Settings**: JSON in `.usersettings/settings.json`
- **Tests**: `test_*.py` pattern in `tests/` directory
- **UI Components**: One class per file in `ui/` directory
- **Core Logic**: Focused modules in `core/` directory

## Import Patterns
- Relative imports within packages (`from .node import Node`)
- Absolute imports for cross-package dependencies
- UI imports from `PySide6.QtWidgets`, `PySide6.QtCore`, `PySide6.QtGui`
- Service imports use async/await patterns with httpx