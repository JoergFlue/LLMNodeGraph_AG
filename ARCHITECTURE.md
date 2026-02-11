# Architecture Overview

AntiGravity is a node-based LLM workflow editor built with Python and PySide6 (Qt). It follows a modular architecture emphasizing separation of concerns, event-driven communication, and extensibility.

## Core Concepts

### MVP Pattern
The application uses the Model-View-Presenter (MVP) pattern to decouple logic from UI:
- **Model**: `Graph`, `Node`, `Link` (in `core/`). Pure data structures.
- **View**: `GraphWidget`, `NodeItem` (in `ui/`). Handles rendering and user input.
- **Presenter**: `GraphController`. Manages business logic and updates the view.

### Event Bus
A central `EventBus` (singleton) handles application-wide communication, reducing direct coupling between components.
- Located in `core/event_bus.py`.
- Signals: `settings_changed`, `file_loaded`, etc.

### Command Pattern
Undo/Redo functionality is implemented via the Command Pattern.
- Base class: `Command` (`core/command.py`).
- Manager: `CommandManager` (`core/command_manager.py`).
- Concrete commands: `AddNodeCommand`, `MoveNodesCommand`, etc.

### Context Assembly
The `ContextAssembler` (`core/assembler.py`) is responsible for traversing the graph and constructing the context window for LLM requests. It handles:
- Ancestry traversal (history).
- Reference resolution (`@ID`).
- Token limit enforcement.

## Directory Structure

- `core/`: Business logic, data models, and controllers.
- `ui/`: Qt widgets and UI components.
- `services/`: Background workers and external integrations (e.g., `LLMWorker`).
- `utils/`: Helper functions.

## Key Flows

1.  **Graph Modification**: User interacts with `GraphWidget` -> `GraphController` adds/removes nodes via `CommandManager` -> Model updates -> View refreshes.
2.  **LLM Generation**: User clicks "Run" -> `LLMWorker` (thread) -> `ContextAssembler` builds prompt -> `LLMProvider` (Strategy) calls API -> Result returned to UI.

