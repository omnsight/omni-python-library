## Omni Python Library

A Python library for interacting with the Omni platform's backend, providing data access layers for various services.

### 🚀 Features

- CRUD operations for Monitoring Sources, OSINT Views, Events, Persons, and more.
- Manages relationships between data entities, like connecting sources to views.
- Built-in permission handling based on user roles.
- Search and query capabilities for indexed data.

### 🛠 Tech Stack

- **Language:** Python 3.12+
- **Database:** ArangoDB
- **Caching:** Redis
- **Package Management:** [uv](https://github.com/astral-sh/uv)
- **Testing:** pytest
- **Formatting:** black, isort

## 📦 Getting Started

### Prerequisites

- [uv](https://github.com/astral-sh/uv)
- Docker

### Installation

1. Clone the repo:
```bash
git clone https://github.com/omnsight/omni-python-library.git
cd omni-python-library
```

2. Install dependencies:
```bash
uv lock --upgrade
uv sync --extra dev
```

## ⚙️ Configuration

Fill the `.env` file with your local or production credentials:
```bash
stage="local"

# ArangoDB
ARANGODB_HOST="http://localhost:8529"
ARANGODB_USERNAME="root"
ARANGODB_PASSWORD="password"
ARANGODB_DB_NAME="test_osint_db"
ARANGODB_EMBEDDING_DIMENSION="384"

# Redis
REDIS_HOST="localhost"
REDIS_PORT="6379"
REDIS_PASSWORD=""

# Embedding Model
EMBEDDING_AI_API_KEY=
EMBEDDING_AI_API_BASE_URL=
EMBEDDING_MODEL=
```

## 📖 Usage

Here is an example of creating a new monitoring source:
```python
from omni_python_library import init_omni_library
from omni_python_library.dal.monitoring_source_data_access_layer import MonitoringSourceDataAccessLayer
from omni_python_library.models import MonitoringSourceMainData, SourceType
from omni_python_library.utils.config import UserRole

# Initialize the library
init_omni_library()

# Define the monitoring source data
ms_data = MonitoringSourceMainData(
    name="My News Source",
    description="A source for news articles.",
    type=SourceType.WEBSITE,
    url="https://news.example.com",
    reliability=85.0,
)

# Create the monitoring source
ms_dal = MonitoringSourceDataAccessLayer()
new_source = ms_dal.create_monitoring_source(
    ms_data, owner="user_id_123", roles=[UserRole.ADMIN]
)

print(f"Created source with ID: {new_source.id}")
```

## Local Development

Refer to [DEVELOPMENT.md](DEVELOPMENT.md) for local development setup.

## 📄 License

Distributed under the Apache-2.0 License. See [LICENSE](./LICENSE) for more information.
