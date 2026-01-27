# Technology Stack

## Core Technologies
- **Python**: 3.12+ required
- **UI Framework**: PySide6 (Qt6 bindings) for professional desktop interface
- **HTTP Client**: httpx for async LLM API calls
- **Package Management**: uv (recommended) or pip
- **Testing**: pytest with async support

## Dependencies
### Production
- `PySide6>=6.10.1` - Qt6 bindings for UI
- `httpx>=0.27.0` - Modern async HTTP client
- `requests>=2.32.5` - HTTP library for compatibility

### Development
- `pytest>=9.0.2` - Testing framework
- `pytest-asyncio>=0.23.5` - Async testing support

## Build System
Uses modern Python packaging with `pyproject.toml`:
- Project metadata and dependencies defined in `pyproject.toml`
- Backward compatibility with `requirements.txt`
- Development dependencies in separate group

## Common Commands

### Setup
```bash
# Using uv (recommended)
uv sync

# Using pip
pip install -r requirements.txt
```

### Running
```bash
# Using uv
uv run python main.py

# Using standard Python
python main.py
```

### Testing
```bash
# Run tests
pytest

# Run with async support
pytest -v
```

### Development
```bash
# Install development dependencies
uv sync --group dev

# Run specific test file
pytest tests/test_specific.py
```

## Configuration
- Settings stored in `.usersettings/settings.json`
- API keys stored in plain text (security consideration)
- Logging configuration in `core/logging_setup.py`