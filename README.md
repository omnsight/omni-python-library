# omni-python-library


## Local Development

This project is managed with [uv](https://github.com/astral-sh/uv).

Install dependencies (including development tools):
```bash
uv sync --extra dev
```

Upgrade dependencies:
```bash
uv lock --upgrade
uv sync
```

Run the application:
```bash
uv run uvicorn src.main:app --reload
```

Run unit tests

```bash
docker compose up -d
python3 -m pytest
docker compose down
```

Format the code using black:
```bash
uv run black .
```
