# Contributing to AntiGravity

We welcome contributions! Please follow these guidelines to ensure code quality and consistency.

## Development Setup

1.  **Environment**: Use `uv` for dependency management.
    ```bash
    uv venv
    uv pip install -r pyproject.toml
    ```
2.  **Running**:
    ```bash
    uv run main.py
    ```

## Code Style

- **Python**: Follow PEP 8.
- **Docstrings**: We use Google-style docstrings.
    - All modules, classes, and methods must have docstrings.
    - We enforce 90% docstring coverage via `interrogate`.
    - Run check: `uv run interrogate -v core`
- **Type Hinting**: Required for all function signatures.

## Pull Request Process

1.  Create a feature branch.
2.  **Ensure tests pass**: 
    - Run unit tests: `uv run pytest tests/test_graph_controller.py` (etc.)
    - Run integration tests: `uv run pytest tests/test_api_integration.py`
3.  Ensure docstring coverage is maintained (>90%).
4.  Submit a PR with a clear description of changes.

## Testing Guidelines

- **Unit Tests**: Focus on individual class logic (e.g., `Graph`, `CommandManager`).
- **Integration Tests**: Use the `AntiGravityAPI` in `core/api.py` to verify end-to-end workflows and UI synchronization.
- **Fixtures**: Use shared fixtures from `tests/conftest.py`.
- **Mocks**: Mock external services (LLM APIs, file systems where appropriate) to ensure tests are fast and reliable.

## Architecture

Please review `ARCHITECTURE.md` before making significant structural changes to understand the core patterns (MVP, Command, Event Bus).
