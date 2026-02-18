# Omni Python Library

[![codecov](https://codecov.io/github/omnsight/omni-python-library/graph/badge.svg?token=WGI02I2208)](https://codecov.io/github/omnsight/omni-python-library)

This repository contains a Python library for interacting with the Omni platform. It provides a data access layer (DAL) for OSINT data, middleware for user authentication, and various utility functions.

## Installation

To install the package, add the following dependency to your `pyproject.toml` file:

```bash
dependencies = [
    "omni-python-library @ git+https://github.com/omnsight/omni-python-library",
]
```

## Usage

Here is a simple example of how to use the library:

```python
from omni_python_library import init_omni_library

def entry_point():
    init_omni_library()
```

```python
from omni_python_library.dal.osint_data_access_layer import OsintDataAccessLayer

OsintDataAccessLayer().query(...)
```

## Local Development

This project is managed with [uv](https://github.com/astral-sh/uv).

Install dependencies (including development tools):
```bash
uv sync --extra dev
```

Upgrade dependencies:
```bash
uv lock --upgrade
uv sync --extra dev

uv run poe clean
```

Run the application:
```bash
uv run uvicorn src.main:app --reload
```

Run unit tests

```bash
# loading .env is necessary for local testing
docker compose up -d --wait
export $(cat .env | xargs) && uv run pytest
docker compose down
```

Format the code using black and isort:
```bash
uv run black .
uv run isort .
```
