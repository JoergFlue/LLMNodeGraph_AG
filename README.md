# AntiGravity: Node-Based LLM Logic Engine

**Stack:** Python 3.12+, PySide6 (Qt), httpx  
**Status:** Professional Prototype / Proof of Concept

## Overview

AntiGravity is an exploration into non-linear LLM interaction. While the industry has settled on the "linear chat" paradigm rooted in 1970s terminal interfaces, AntiGravity looks towards the VFX and Gaming industries for inspiration, using a **Directed Acyclic Graph (DAG)** to structure AI logic.

Developed as a "vibe coding" experiment using Google AntiGravity, this tool allows you to branch, merge, and visualize complex LLM workflows that would be impossible to manage in a standard chat box.

![AntiGravity Main Window](docs/Screenshot_2026-01-09.png)

## Why a Node Graph?

- **Non-Linear Branching**: Explore multiple "what-if" scenarios simultaneously without losing context.
- **Smart Context Assembly**: Inherit history from specific parent nodes or @reference connected outputs.
- **Visual Token Management**: Real-time meters show exactly how much context you're sending to the model.
- **Multi-Provider Hub**: Seamlessly mix nodes from Ollama (local), OpenAI, Gemini, and OpenRouter in a single canvas.

## Key Features

- **Professional Canvas**: Drag-and-drop node editor with smooth pan/zoom and resizable components.
- **MVP Architecture**: Clean separation between business logic (`core/`) and UI rendering (`ui/`).
- **Command System**: Complete Undo/Redo support for every graph operation.
- **Queue-Based execution**: Run multiple nodes concurrently with real-time status indicators and timers.
- **High-Level API**: Includes a developer API (`core/api.py`) for automated testing and advanced flow control.

## Installation

### Prerequisites
- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended)

### Setup
```bash
# Clone the repository
git clone <repository-url>
cd AntiGravity

# Install dependencies and run
uv sync
uv run python main.py
```

## Quick Start

1. **Add Nodes**: Use `Ctrl+N` or right-click the canvas.
2. **Connect**: Drag from an output port (right) to an input area (left).
3. **Configure**: Click the model label on a node to set specific provider/model overrides.
4. **Reference**: Use `@NodeName` in your prompt to pull in data from connected nodes.
5. **Run**: Click the "RUN" button or `Ctrl+Enter` to execute the node.

## Architecture & Contribution

This project follows a strict modular design:
- **Core**: Graph logic, command pattern, and context assembly.
- **UI**: Customized Qt components using a centralized theme system.
- **Services**: Async workers for non-blocking LLM requests.

For a deeper dive into the system design, check out [ARCHITECTURE.md](ARCHITECTURE.md).
Contributions are welcome—please see [CONTRIBUTING.md](CONTRIBUTING.md) for testing and style guidelines.

---

**AntiGravity** - *Because linear chat is just a bit boring.*
