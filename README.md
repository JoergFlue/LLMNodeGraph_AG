# AntiGravity: Branching LLM Logic Engine

**Version:** 0.1.0  
**Stack:** Python 3.12+, PySide6 (Qt), httpx, JSON  
**Type:** Professional Node-Based Desktop Application

## Overview

AntiGravity is a sophisticated local-first desktop application for non-linear LLM interactions. It provides a professional node-based editor that structures conversations as a **Directed Acyclic Graph (DAG)**, enabling complex branching logic, advanced context management, and seamless multi-provider LLM integration.

Unlike traditional linear chat interfaces, AntiGravity offers:
- **Visual Node-Based Workflow**: Professional drag-and-drop canvas with resizable nodes
- **Multi-Document Interface**: Work with multiple graph projects simultaneously in tabs
- **Advanced Context Assembly**: Smart context inheritance with explicit `@ID` referencing
- **Intelligent Token Management**: Real-time context payload visualization and limits
- **Queue-Based Execution**: Concurrent LLM requests with cancellation support
- **Complete Undo/Redo System**: Full command pattern implementation for all operations
- **Multi-Provider Support**: Ollama, OpenAI, Google Gemini, and OpenRouter integration

![AntiGravity Main Window](docs/Screenshot_2026-01-09.png)

## Key Features

### 🎯 Core Capabilities

- **Professional Node Editor**: Advanced resizable nodes with visual status indicators and execution overlays
- **Multi-Document Interface**: Tab-based workspace for managing multiple graph projects simultaneously
- **DAG-Based Context Flow**: Nodes connect in a directed acyclic graph with automatic cycle prevention
- **Smart Context Assembly**: Intelligent history gathering from parent nodes with configurable trace depth
- **Real-Time Token Management**: Visual context payload meters with intelligent truncation and warnings
- **Queue-Based Execution**: Concurrent LLM processing with task queuing, cancellation, and progress tracking
- **Complete Undo/Redo System**: Full command pattern implementation supporting all graph operations
- **Physical Connection Constraint**: Enforces explicit wiring - can only reference nodes with physical connections

### 🔧 Advanced Features

- **Interactive Node Resizing**: Drag handles for both node dimensions and internal text field heights
- **Visual Execution Feedback**: Real-time spinners, timers, and status overlays during LLM processing
- **Graph Merging**: Import and merge graphs from other files with automatic ID collision resolution
- **Copy/Paste/Duplicate**: Full clipboard operations preserving internal node connections
- **Model Auto-Discovery**: Background fetching of available models from all configured providers
- **Connection Testing**: Built-in connectivity verification for all LLM providers
- **Advanced Settings**: Multi-tab configuration interface with persistent storage

### 🌐 Multi-Provider Support

- **Ollama**: Local models (Llama, Mistral, CodeLlama, etc.) with auto-discovery
- **OpenAI**: GPT-4, GPT-3.5-turbo, and latest models with API key management
- **Google Gemini**: Gemini-1.5-flash, Gemini-1.5-pro with secure key storage
- **OpenRouter**: Access to hundreds of models through unified API
- **Smart Provider Detection**: Automatic provider selection based on model names

## Architecture

AntiGravity follows a sophisticated modular architecture with advanced design patterns:

### Core Modules (`core/`)

- **`node.py`**: Advanced data models with comprehensive serialization
  - `Node`: Complete LLM interaction model with config, dimensions, and cached outputs
  - `Link`: Connection model with UUID-based identification
  - `NodeConfig`: Provider-specific configuration with token limits and trace depth

- **`graph.py`**: Sophisticated graph state management
  - Advanced ID collision detection and resolution
  - Intelligent graph merging with positioning logic
  - Comprehensive validation and error recovery
  - Name uniqueness enforcement with auto-generation

- **`assembler.py`**: Advanced context assembly engine
  - Primary parent concept for linear history inheritance
  - Implicit context from unreferenced connected inputs
  - Sophisticated token budgeting with priority-based truncation
  - Real-time context payload calculation

- **`command_manager.py`**: Complete undo/redo system
  - Command pattern implementation for all operations
  - Configurable stack size with automatic cleanup
  - Operation descriptions for UI feedback

- **`graph_controller.py`**: Graph operations controller (MVP pattern)
  - Manages all graph file operations (create, load, save, merge)
  - Handles dirty state tracking and file path management
  - Separates business logic from UI concerns
  - Fully tested with 33 unit tests

- **`tab_controller.py`**: Tab lifecycle controller (MVP pattern)
  - Manages tab creation, closing, and activation
  - Coordinates between tabs and graph controllers
  - Emits signals for UI synchronization
  - Fully tested with 37 unit tests

### UI Modules (`ui/`)

- **`main_window.py`**: Multi-document interface orchestration
  - Tab-based workspace management
  - Comprehensive menu system with keyboard shortcuts
  - Graph merging and file operations

- **`editor_tab.py`**: Individual graph editor with full feature set
  - Complete node and wire management
  - Copy/paste operations with link preservation
  - Queue integration and execution management

- **`canvas.py`**: Professional graphics scene and view
  - Grid background with smooth pan/zoom
  - Context menus and interaction handling
  - Optimized rendering for large graphs

- **`node_item.py`**: Advanced visual node representation
  - Resizable nodes with drag handles
  - Interactive text editors with focus management
  - Visual status overlays and execution feedback
  - Context menus and settings integration

- **`settings_dialog.py`**: Comprehensive configuration interface
  - Multi-tab provider configuration
  - Background model fetching with progress indication
  - Connection testing and validation

- **`theme.py`**: Centralized styling system
  - Consistent color schemes and typography
  - Configurable UI constants and spacing

### Services (`services/`)

- **`worker.py`**: Advanced async LLM integration
  - Full async/await implementation with httpx
  - Support for all major providers with unified interface
  - Comprehensive error handling and timeout management
  - Cancellation support for running requests

- **`llm_queue_manager.py`**: Sophisticated task management
  - Concurrent request handling with queuing
  - Task cancellation and state management
  - Progress tracking and status reporting

- **`fetch_worker.py`**: Background model discovery
  - Async model fetching from all providers
  - Error handling and retry logic
  - UI integration with progress feedback

## Installation

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended) or pip

### Dependencies

- **PySide6**: Modern Qt6 bindings for professional UI
- **httpx**: Async HTTP client for LLM API calls
- **pytest**: Testing framework for development

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AntiGravity
   ```

2. **Install dependencies**
   
   Using uv (recommended):
   ```bash
   uv sync
   ```
   
   Using pip:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure LLM Providers** (see Configuration section)

## Usage

### Starting the Application

```bash
# Using uv
uv run python main.py

# Using standard Python
python main.py
```

### Basic Workflow

1. **Create Projects**: Start with "New" or open existing graph files in separate tabs
2. **Add Nodes**: Click "Add Node" in toolbar, right-click canvas, or use Ctrl+N
3. **Connect Nodes**: Drag from output port (right side) to input area (left side) of target node
4. **Configure Nodes**: Double-click model label to change provider/model settings
5. **Write Prompts**: Click in prompt area to edit, use `@NodeID` to reference connected nodes
6. **Execute**: Click "RUN" button or Ctrl+Enter in prompt editor
7. **Monitor Progress**: Watch real-time execution status with spinners and timers
8. **Manage Results**: View formatted output, copy/paste nodes, undo/redo operations

### Advanced Features

#### Multi-Document Workflow
- **Multiple Tabs**: Work with several graph projects simultaneously
- **Graph Merging**: Import nodes from other files via "Merge Graph" (Ctrl+Shift+O)
- **Cross-Project Operations**: Copy nodes between different graph tabs

#### Node Management
- **Resizing**: Drag corner handle to resize nodes, drag separator to adjust text field heights
- **Organization**: Use copy (Ctrl+C), cut (Ctrl+X), paste (Ctrl+V), duplicate (Alt+D)
- **Naming**: Press F2 or double-click header to rename nodes with validation

#### Context Control
- **Trace Depth**: Controls parent generation inclusion (0=none, 1=immediate, 2+=ancestors)
- **Token Budgets**: Set per-node limits or use global default, with visual payload meters
- **Reference System**: Use `@NodeID` syntax - only works with physically connected nodes

#### Execution Management
- **Queue System**: Multiple nodes can run concurrently with automatic queuing
- **Cancellation**: Click "CANCEL" button or use queue manager to stop running tasks
- **Status Tracking**: Visual indicators show IDLE (green), DIRTY (yellow), RUNNING (spinner)

### Keyboard Shortcuts

#### File Operations
- **Ctrl+Alt+N**: New graph
- **Ctrl+O**: Open graph file
- **Ctrl+S**: Save current tab
- **Ctrl+Shift+S**: Save current tab as
- **Ctrl+W**: Close current tab
- **Ctrl+Shift+O**: Merge graph into current tab

#### Edit Operations
- **Ctrl+Z**: Undo last operation
- **Ctrl+Y**: Redo last undone operation
- **Ctrl+N**: Add new node
- **Ctrl+C**: Copy selected nodes
- **Ctrl+X**: Cut selected nodes
- **Ctrl+V**: Paste nodes
- **Alt+D**: Duplicate selected nodes
- **F2**: Rename selected node
- **Delete**: Delete selected nodes

#### Navigation
- **Middle Mouse**: Pan canvas
- **Mouse Wheel**: Zoom in/out
- **Ctrl+Enter**: Run node (when editing prompt)

### Context Menus

- **Node Right-Click**: Run, Rename, Copy, Cut, Delete
- **Canvas Right-Click**: Add Node, Paste (if clipboard has nodes)
- **Model Label Click**: Open node-specific provider/model settings

## Configuration

### Settings Dialog

Access via **File → Settings** or toolbar icon.

#### Ollama Tab
- **Host**: Ollama server address (default: `localhost`)
- **Port**: Ollama server port (default: `11434`)
- **Model**: Default model with auto-discovery (e.g., `llama3`, `mistral`)
- **Fetch Models**: Background discovery of available local models
- **Test Connection**: Verify Ollama server connectivity

#### OpenAI Tab
- **API Key**: Your OpenAI API key (or set `OPENAI_API_KEY` env var)
- **Model**: Default model with auto-discovery (e.g., `gpt-4o`, `gpt-4-turbo`)
- **Fetch Models**: Background retrieval of available OpenAI models
- **Test Connection**: Verify API key and connectivity

#### Gemini Tab
- **API Key**: Your Google Gemini API key
- **Model**: Default model with auto-discovery (e.g., `gemini-1.5-flash`, `gemini-1.5-pro`)
- **Fetch Models**: Background retrieval of available Gemini models
- **Test Connection**: Verify API key and connectivity

#### OpenRouter Tab
- **API Key**: Your OpenRouter API key for access to hundreds of models
- **Model**: Default model with full catalog discovery
- **Fetch Models**: Background retrieval of entire OpenRouter model catalog
- **Test Connection**: Verify API key and service connectivity

#### General Tab
- **Default Provider**: System-wide default (Ollama, OpenAI, Gemini, OpenRouter)
- **Global Token Limit**: Default context limit for new nodes (default: 16,384)
- **Undo Stack Size**: Maximum number of operations to remember (default: 50)

### Configuration Storage

Settings are stored in a local JSON file:
- **Location**: `.usersettings/settings.json` within the repository.

> [!WARNING]
> **Security Warning**: API keys for OpenAI and Gemini are currently saved in **clear text** within the `settings.json` file. While this folder is included in `.gitignore` to prevent accidental commits, ensure your local environment is secure.

## File Format

Graphs are saved as JSON files with comprehensive metadata and validation:

```json
{
  "version": "2.0",
  "app_settings": {
    "global_token_limit": 16384
  },
  "nodes": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "type": "LLM_Node",
      "pos": [400, 300],
      "size": [350, 500],
      "text_heights": [120, 180],
      "config": {
        "model": "gpt-4o",
        "provider": "OpenAI",
        "max_tokens": 32000,
        "trace_depth": 2
      },
      "prompt": "Analyze the following data from @upstream_node...",
      "cached_output": "Based on the analysis of the provided data...",
      "is_dirty": false,
      "name": "Data_Analysis_0001",
      "inputs": ["link-uuid-1", "link-uuid-2"]
    }
  ],
  "links": [
    {
      "id": "link-uuid-1",
      "source": "source-node-uuid",
      "target": "target-node-uuid"
    }
  ]
}
```

### Advanced Features
- **ID Collision Detection**: Automatic UUID remapping when loading files with duplicate IDs
- **Name Collision Handling**: Smart renaming when merging graphs with duplicate node names
- **Validation**: Comprehensive validation with detailed error reporting and recovery
- **Backward Compatibility**: Handles legacy file formats with automatic migration

## Development

### Project Structure

```
AntiGravity/
├── core/                    # Core logic and data models
│   ├── assembler.py        # Advanced context assembly engine
│   ├── command.py          # Command pattern implementations
│   ├── command_manager.py  # Undo/redo system management
│   ├── graph.py            # Sophisticated graph state management
│   ├── graph_controller.py # Graph operations controller (MVP)
│   ├── tab_controller.py   # Tab lifecycle controller (MVP)
│   ├── logging_setup.py    # Multi-level logging configuration
│   ├── node.py             # Advanced node and link models
│   └── settings_manager.py # Persistent configuration management
├── services/               # Background services and workers
│   ├── fetch_worker.py     # Async model discovery workers
│   ├── llm_queue_manager.py # Task queuing and execution management
│   └── worker.py           # Advanced async LLM integration
├── ui/                     # Professional user interface
│   ├── canvas.py           # Graphics scene with advanced interactions
│   ├── editor_tab.py       # Multi-document tab management
│   ├── log_window.py       # Dedicated logging interface
│   ├── main_window.py      # Application orchestration
│   ├── node_item.py        # Advanced visual node components
│   ├── node_settings_dialog.py # Per-node configuration
│   ├── settings_dialog.py  # Comprehensive settings interface
│   ├── theme.py            # Centralized styling system
│   └── wire_item.py        # Bezier curve connection rendering
├── tests/                  # Comprehensive test suite
│   ├── conftest.py         # Shared pytest fixtures
│   ├── test_graph_controller.py    # GraphController tests (33 tests)
│   ├── test_tab_controller.py      # TabController tests (37 tests)
│   ├── test_main_window_integration.py # Integration tests (18 tests)
│   └── test_ui_functionality.py    # UI component tests
├── main.py                 # Application entry point
├── pyproject.toml          # Modern Python project configuration
└── requirements.txt        # Pip compatibility
```

### Key Design Patterns

- **Command Pattern**: Complete undo/redo system for all graph operations
- **Observer Pattern**: Signal/slot architecture for loose coupling between components
- **MVP Pattern**: Model-View-Presenter with controller layer for business logic separation
- **Queue Pattern**: Sophisticated task management for concurrent LLM processing
- **Singleton Pattern**: Centralized settings and configuration management
- **MVC Architecture**: Clear separation between data models, business logic, and presentation
- **Factory Pattern**: Dynamic node and component creation with proper initialization
- **Strategy Pattern**: Pluggable provider system for different LLM services

### Extending the Application

#### Adding a New LLM Provider

1. **Settings Integration**: Add provider tab in `ui/settings_dialog.py`
2. **Worker Implementation**: Add API integration method in `services/worker.py`
3. **Model Discovery**: Implement model fetching in `services/fetch_worker.py`
4. **Provider Detection**: Update heuristics in worker routing logic
5. **Testing**: Add connection testing functionality

#### Adding Advanced Node Features

1. **Data Model**: Update `Node` dataclass in `core/node.py`
2. **Serialization**: Modify `to_dict()` and `from_dict()` methods
3. **UI Components**: Enhance visual representation in `ui/node_item.py`
4. **Commands**: Create new command classes for undo/redo support
5. **Settings**: Add configuration options in node settings dialog

#### Implementing Custom Themes

1. **Theme Definition**: Extend `ui/theme.py` with new color schemes
2. **Style Application**: Update component stylesheets
3. **Settings Integration**: Add theme selection to settings dialog
4. **Persistence**: Store theme preferences in settings manager

## Known Limitations

The following are acknowledged limitations in the current release:

### Resolved in Current Version ✅
- **Undo/Redo System**: ✅ Complete command pattern implementation
- **ID Collision Handling**: ✅ Automatic UUID remapping on file operations
- **Node Selection Feedback**: ✅ Visual selection indicators with borders and highlights
- **Async HTTP Requests**: ✅ Full httpx and asyncio implementation with cancellation

### Current Limitations
1. **@ID Autocomplete**: Typing `@` doesn't show popup with available connected node IDs
2. **Streaming Responses**: No real-time display of LLM output as it's generated
3. **Export Formats**: Limited to JSON - no Markdown, PDF, or other format export
4. **Advanced Text Editor**: Basic QTextEdit without syntax highlighting or code features
5. **API Key Security**: Keys stored in plain text (though in gitignored directory)

### Performance Considerations
- **Large Graphs**: No specific optimizations for graphs with 100+ nodes
- **Memory Usage**: Full output text stored in memory without lazy loading
- **Rendering**: Complete scene refresh on updates rather than incremental updates

## Roadmap

### Short-term Enhancements
- [ ] **@ID Autocomplete**: Popup completion for connected node references
- [ ] **Streaming Display**: Real-time LLM response visualization
- [ ] **Export System**: Markdown, PDF, and diagram export functionality
- [ ] **API Key Encryption**: Secure credential storage using OS keychain
- [ ] **Advanced Text Editor**: Syntax highlighting and code editing features

### Medium-term Features
- [ ] **Performance Optimization**: Large graph handling and incremental rendering
- [ ] **Plugin System**: Custom node types and provider extensions
- [ ] **Collaboration**: Multi-user editing and version control integration
- [ ] **Templates**: Node and graph templates for common workflows
- [ ] **Search & Filter**: Advanced node discovery and organization tools

### Long-term Vision
- [ ] **Cloud Sync**: Optional cloud storage and synchronization
- [ ] **Mobile Companion**: Tablet/mobile app for graph viewing and basic editing
- [ ] **AI Assistant**: Intelligent suggestions for graph structure and optimization
- [ ] **Integration APIs**: REST API for external tool integration
- [ ] **Advanced Analytics**: Usage patterns and performance insights

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes with clear commit messages
4. Test thoroughly
5. Submit a pull request

## License

[Specify your license here]

## Support

For issues, questions, or feature requests, please [open an issue](link-to-issues).

## Acknowledgments

- Built with [PySide6](https://doc.qt.io/qtforpython-6/) for professional desktop UI
- HTTP client powered by [httpx](https://www.python-httpx.org/) for modern async requests
- Inspired by node-based editors like ComfyUI, Blender's shader editor, and Unreal Engine blueprints
- LLM provider integrations: [Ollama](https://ollama.ai/), [OpenAI](https://openai.com/), [Google Gemini](https://ai.google.dev/), and [OpenRouter](https://openrouter.ai/)
- Testing framework: [pytest](https://pytest.org/) with async support

---

**AntiGravity** - Professional node-based LLM interaction beyond linear conversations.
