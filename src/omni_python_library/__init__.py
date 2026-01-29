from omni_python_library.clients.arangodb import ArangoDBClient
from omni_python_library.clients.openai import OpenAIClient
from omni_python_library.clients.redis import RedisClient
from omni_python_library.dal.osint_data_access_layer import OsintDataAccessLayer
from omni_python_library.dal.view_data_access_layer import ViewDataAccessLayer
from omni_python_library.dal.monitoring_source_data_access_layer import MonitoringSourceDataAccessLayer
from omni_python_library.utils.config_registry import ConfigRegistry, LLMConstant


def init_omni_library() -> None:
    """
    Initializes all clients and the Data Access Layer (DAL) for the library.

    This function sets up the singletons for ArangoDB, Redis, OpenAI, and the OSINT DAL.
    It relies on environment variables for configuring ArangoDB and Redis connections.

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
        host=ConfigRegistry().get("ARANGODB_HOST"),
        username=ConfigRegistry().get("ARANGODB_USERNAME"),
        password=ConfigRegistry().get("ARANGODB_PASSWORD"),
        db_name=ConfigRegistry().get("ARANGODB_DB_NAME"),
        embedding_dimension=int(ConfigRegistry().get("ARANGODB_EMBEDDING_DIMENSION")),
    )

    # Initialize Redis Client
    RedisClient().init(
        host=ConfigRegistry().get("REDIS_HOST"),
        port=int(ConfigRegistry().get("REDIS_PORT")),
        db=int(ConfigRegistry().get("REDIS_DB")),
        password=ConfigRegistry().get("REDIS_PASSWORD"),
    )

    # Initialize OpenAI Client Wrapper
    OpenAIClient().init()
    OpenAIClient().add_client(
        model_use=LLMConstant.EMBEDDING,
        api_key=ConfigRegistry().get("EMBEDDING_AI_API_KEY"),
        model=ConfigRegistry().get("EMBEDDING_MODEL"),
    )

    # Initialize DAL
    OsintDataAccessLayer().init()
    ViewDataAccessLayer().init()
    MonitoringSourceDataAccessLayer().init()
