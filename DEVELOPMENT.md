## 🛠️ Installation Guide

This project is managed with [uv](https://github.com/astral-sh/uv).

Install dependencies (including development tools):
```bash
uv sync --extra dev
```

Upgrade dependencies:
```bash
uv run poe clean
uv lock --upgrade
uv sync --extra dev
```

## 🧪 Running Unit Tests

Run unit tests

```bash
# loading .env is necessary for local testing
docker compose up -d --wait
export $(cat .env | xargs) && uv run pytest
docker compose down
```

## ✨ Formatting Code

Format the code using black and isort:
```bash
uv run black .
uv run isort .
```
