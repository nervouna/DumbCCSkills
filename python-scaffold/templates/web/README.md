# {{project_name}}

{{description}}

## Setup

```bash
uv sync
```

## Usage

```bash
uv run python -m {{project_name_snake}}       # Start server
# or
uv run uvicorn {{project_name_snake}}.app:create_app --factory --reload
```

## Development

```bash
uv run pytest          # Run tests
uv run ruff check .    # Lint
uv run mypy .          # Type check
```
