# AntiGravity: Branching LLM Logic Engine

**Version:** 0.1.0  
**Stack:** Python 3.12+, PySide6 (Qt), JSON  
**Type:** Standalone Desktop Application

## Overview

AntiGravity is a local-first desktop application for non-linear LLM interactions. It allows users to structure conversations as a **Directed Acyclic Graph (DAG)**, enabling complex branching logic, context management, and multi-provider LLM integration.

Unlike traditional linear chat interfaces, AntiGravity lets you:
- Create branching conversation paths
- Reference specific nodes in your prompts using `@ID` syntax
- Control context inheritance with trace depth
- Manage token budgets per node
- Work with multiple LLM providers (Ollama, OpenAI, Google Gemini)

![AntiGravity Main Window](docs/Screenshot_2026-01-09.png)

## Key Features

### 🎯 Core Capabilities

- **Visual Node-Based Interface**: Drag-and-drop canvas with pan/zoom for organizing conversation flows
- **DAG-Based Context**: Nodes connect in a directed acyclic graph, preventing circular dependencies
- **Smart Context Assembly**: Automatically gathers history from parent nodes up to configurable trace depth
- **Token Budget Management**: Per-node and global token limits with intelligent truncation
- **Multi-Provider Support**: Seamlessly switch between Ollama, OpenAI, and Google Gemini
- **Dirty State Tracking**: Visual indicators show when nodes need re-execution
- **Explicit Referencing**: Use `@NodeID` syntax to reference specific nodes in prompts

### 🔧 Technical Features

- **Physical Connection Constraint**: Can only reference nodes that are physically connected via wires
- **Passive Dirty State**: Nodes can execute using cached parent outputs without forcing re-runs
- **Context Prioritization**: Keeps current prompt and explicit references, truncates history if needed
- **Async Worker Threads**: Non-blocking LLM API calls prevent UI freezing
- **JSON Persistence**: Save and load entire conversation graphs
- **Comprehensive Logging**: Multi-level logging with dedicated log window

## Architecture

AntiGravity follows a modular MVC architecture:

### Core Modules (`core/`)

- **`node.py`**: Data models for nodes and links
  - `Node`: Represents an LLM interaction with config, prompt, and cached output
  - `Link`: Represents connections between nodes
  - `NodeConfig`: Configuration for model, max_tokens, and trace_depth

- **`graph.py`**: Graph state management
  - Manages nodes and links collections
  - Handles dirty state propagation
  - Provides serialization/deserialization

- **`assembler.py`**: Context assembly logic
  - Gathers history from parent nodes
  - Resolves `@ID` references
  - Enforces token limits with smart truncation

### UI Modules (`ui/`)

- **`main_window.py`**: Main application window and orchestration
- **`canvas.py`**: Graphics scene and view with grid background
- **`node_item.py`**: Visual node representation with ports, prompt editor, and controls
- **`wire_item.py`**: Bezier curve connections between nodes
- **`settings_dialog.py`**: Multi-tab settings for LLM providers
- **`log_window.py`**: Floating window for application logs

### Services (`services/`)

- **`worker.py`**: Background thread for LLM API calls
  - Supports Ollama, OpenAI, and Google Gemini
  - Handles streaming and error reporting
  - Emits signals for UI updates

## Installation

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended) or pip

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

1. **Create Nodes**: Click "Add Node" in the toolbar or right-click canvas → "Add Node"
2. **Connect Nodes**: Click and drag from a node's output port (right side) to another node's input area (left side)
3. **Write Prompts**: Click on a node to edit its prompt in the text editor
4. **Reference Nodes**: Use `@NodeID` syntax to reference connected nodes (e.g., "Summarize @A1")
5. **Run Nodes**: Click the "RUN" button on a node to execute it
6. **View Results**: Output appears in the node's output area

### Context Management

- **Trace Depth**: Controls how many parent generations to include in context
  - `0`: No history, only current prompt and explicit references
  - `1`: Include immediate parent's output
  - `2+`: Include parent, grandparent, etc.

- **Token Limits**: Set per-node or use global default (16,384)
  - System prioritizes: Current prompt → Explicit `@ID` refs → History
  - Oldest history is truncated first if budget exceeded

### Keyboard Shortcuts

- **Ctrl+C**: Copy selected nodes
- **Ctrl+X**: Cut selected nodes
- **Ctrl+V**: Paste nodes
- **Ctrl+D**: Duplicate selected nodes
- **Delete**: Delete selected nodes
- **Middle Mouse**: Pan canvas
- **Mouse Wheel**: Zoom in/out

### Context Menus

- **Node Right-Click**: Run, Copy, Cut, Delete
- **Canvas Right-Click**: Add Node, Paste

## Configuration

### Settings Dialog

Access via **File → Settings** or toolbar icon.

#### Ollama Tab
- **Host**: Ollama server address (default: `localhost`)
- **Port**: Ollama server port (default: `11434`)
- **Model**: Default model (e.g., `llama3`, `mistral`)
- **Fetch Models**: Auto-discover available models
- **Test Connection**: Verify Ollama is running

#### OpenAI Tab
- **API Key**: Your OpenAI API key (or set `OPENAI_API_KEY` env var)
- **Model**: Default model (e.g., `gpt-4o`, `gpt-4-turbo`)
- **Fetch Models**: List available models
- **Test Connection**: Verify API key

#### Gemini Tab
- **API Key**: Your Google Gemini API key
- **Model**: Default model (e.g., `gemini-1.5-flash`, `gemini-1.5-pro`)
- **Fetch Models**: List available models
- **Test Connection**: Verify API key

### Configuration Storage

Settings are stored in a local JSON file:
- **Location**: `.usersettings/settings.json` within the repository.

> [!WARNING]
> **Security Warning**: API keys for OpenAI and Gemini are currently saved in **clear text** within the `settings.json` file. While this folder is included in `.gitignore` to prevent accidental commits, ensure your local environment is secure.

## File Format

Graphs are saved as JSON files with the following structure:

```json
{
  "version": "2.0",
  "app_settings": {
    "global_token_limit": 16384
  },
  "nodes": [
    {
      "id": "a1b2c3d4",
      "type": "LLM_Node",
      "pos": [400, 300],
      "config": {
        "model": "gpt-4o",
        "max_tokens": 32000,
        "trace_depth": 2
      },
      "prompt": "Analyze the following...",
      "cached_output": "Based on the analysis...",
      "is_dirty": false,
      "inputs": ["link-id-1", "link-id-2"]
    }
  ],
  "links": [
    {
      "id": "link-id-1",
      "source": "source-node-id",
      "target": "target-node-id"
    }
  ]
}
```

## Development

### Project Structure

```
AntiGravity/
├── core/                 # Core logic and data models
│   ├── __init__.py
│   ├── assembler.py     # Context assembly
│   ├── graph.py         # Graph management
│   ├── logging_setup.py # Logging configuration
│   └── node.py          # Node/Link models
├── services/            # Background services
│   ├── __init__.py
│   └── worker.py        # LLM worker thread
├── ui/                  # User interface
│   ├── __init__.py
│   ├── canvas.py        # Graphics scene/view
│   ├── log_window.py    # Log viewer
│   ├── main_window.py   # Main window
│   ├── node_item.py     # Node visual component
│   ├── settings_dialog.py # Settings UI
│   └── wire_item.py     # Connection visual
├── main.py              # Application entry point
├── pyproject.toml       # Project metadata
└── uv.lock              # Dependency lock file
```

### Key Design Patterns

- **MVC Architecture**: Clear separation between data (core), logic (services), and presentation (ui)
- **Signal/Slot**: Qt signals for loose coupling between components
- **Worker Thread Pattern**: Background threads for blocking I/O operations
- **Dirty Flag Pattern**: Efficient change tracking and propagation

### Extending the Application

#### Adding a New LLM Provider

1. Add provider settings in `ui/settings_dialog.py`
2. Implement API call method in `services/worker.py`
3. Add routing logic in `worker.run()`

#### Adding Node Features

1. Update `Node` dataclass in `core/node.py`
2. Modify serialization in `to_dict()` and `from_dict()`
3. Update UI in `ui/node_item.py`

## Known Limitations (MVP Scope)

The following are acknowledged limitations for the initial release:

1. **Text Editor**: Standard `QTextEdit` without code syntax highlighting
2. **Concurrency**: Synchronous `requests` in `QThread` instead of full async
3. **Undo/Redo**: No undo/redo system for graph operations
4. **ID Collisions**: Merging JSON files with duplicate IDs not supported
5. **Autocomplete**: `@ID` autocomplete not yet implemented
6. **Testing**: No automated test suite currently

## Roadmap

Future enhancements being considered:

- [ ] Autocomplete for `@ID` references
- [ ] Syntax highlighting in prompt editor
- [ ] Undo/redo system
- [ ] Export to various formats (Markdown, PDF)
- [ ] Node templates and snippets
- [ ] Collaborative editing
- [ ] Plugin system for custom nodes
- [ ] Advanced visualization options
- [ ] Performance optimizations for large graphs

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

- Built with [PySide6](https://doc.qt.io/qtforpython-6/)
- Inspired by node-based editors like ComfyUI and Blender's shader editor
- LLM provider integrations: Ollama, OpenAI, Google Gemini

---

**AntiGravity** - Elevate your LLM interactions beyond linear conversations.
