import os

from omni_python_library.clients.arangodb import ArangoDBClient
from omni_python_library.clients.openai import OpenAIClient
from omni_python_library.clients.redis import RedisClient
from omni_python_library.dal.osint_data_access_layer import OsintDataAccessLayer


def init_omni_library() -> None:
    """
    Initializes all clients and the Data Access Layer (DAL) for the library.

    This function sets up the singletons for ArangoDB, Redis, OpenAI, and the OSINT DAL.
    It relies on environment variables for configuring ArangoDB and Redis connections.

    Environment Variables:
        ArangoDB:
            - ARANGODB_HOST: URL of the ArangoDB server (default: "http://localhost:8529")
            - ARANGODB_USERNAME: Username for authentication (default: "root")
            - ARANGODB_PASSWORD: Password for authentication (default: "")
            - ARANGODB_DB_NAME: Database name (default: "osint_db")
            - ARANGODB_EMBEDDING_DIMENSION: Dimension for vector embeddings (default: 1536)

        Redis:
            - REDIS_HOST: Hostname of the Redis server (default: "localhost")
            - REDIS_PORT: Port of the Redis server (default: 6379)
            - REDIS_DB: Redis database index (default: 0)
            - REDIS_PASSWORD: Redis password (default: None)

    OpenAI Client Usage:
        The OpenAI client wrapper is initialized but requires explicit registration of clients
        for different model uses (e.g., LLM, Embedding) using `OpenAIClient().add_client`.

        Example:
            from omni_python_library.clients.openai import OpenAIClient

            # Register an embedding client (REQUIRED for DAL to generate embeddings)
            OpenAIClient().add_client(
                model_use="embedding",
                api_key="your-api-key",
                model="text-embedding-3-small"
            )

            # Register an LLM client
            OpenAIClient().add_client(
                model_use="agent",
                api_key="your-api-key",
                model="gpt-4o"
            )

        Note:
            The `embedding` client MUST be registered if you intend to use DAL methods
            that create entities (e.g., `create_person`, `create_event`), as they automatically
            generate embeddings for the stored data.
    """
    # Initialize ArangoDB Client
    ArangoDBClient().init(
        host=os.getenv("ARANGODB_HOST", "http://localhost:8529"),
        username=os.getenv("ARANGODB_USERNAME", "root"),
        password=os.getenv("ARANGODB_PASSWORD", ""),
        db_name=os.getenv("ARANGODB_DB_NAME", "osint_db"),
        embedding_dimension=int(os.getenv("ARANGODB_EMBEDDING_DIMENSION", "1536")),
    )

    # Initialize Redis Client
    RedisClient().init(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=int(os.getenv("REDIS_DB", "0")),
        password=os.getenv("REDIS_PASSWORD"),
    )

    # Initialize OpenAI Client Wrapper
    OpenAIClient().init()

    # Initialize DAL
    OsintDataAccessLayer().init()
