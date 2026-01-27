# Product Overview

AntiGravity is a professional desktop application for non-linear LLM interactions using a node-based visual editor. It structures conversations as a Directed Acyclic Graph (DAG), enabling complex branching logic and advanced context management.

## Core Concept
- **Visual Node-Based Workflow**: Drag-and-drop canvas with resizable nodes
- **Multi-Document Interface**: Tab-based workspace for multiple graph projects
- **DAG-Based Context Flow**: Nodes connect in directed acyclic graphs with cycle prevention
- **Smart Context Assembly**: Intelligent history gathering from parent nodes with configurable trace depth
- **Queue-Based Execution**: Concurrent LLM processing with cancellation support

## Key Features
- Professional node editor with visual status indicators
- Real-time token management with visual payload meters
- Complete undo/redo system using command pattern
- Multi-provider LLM support (Ollama, OpenAI, Google Gemini, OpenRouter)
- Physical connection constraint - can only reference nodes with explicit wiring
- Advanced context assembly with `@NodeID` referencing system

## Target Users
Developers, researchers, and power users who need sophisticated LLM interaction workflows beyond simple linear chat interfaces.