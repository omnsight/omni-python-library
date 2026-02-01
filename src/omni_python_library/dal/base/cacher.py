import json
import logging
from typing import Any, Optional

from cachetools import TTLCache

from omni_python_library.clients.redis import RedisClient
from omni_python_library.utils import InternalError, Singleton

logger = logging.getLogger(__name__)


class Cacher(Singleton):
    def init(self, expiration_seconds: int = 5):
        super().init()
        self._local_cache: TTLCache = TTLCache(maxsize=1000, ttl=expiration_seconds)

    def get(self, key: str) -> Optional[Any]:
        # Check local cache first
        if key in self._local_cache:
            logger.debug(f"Key {key} found in local cache")
            return self._local_cache[key]

        # Check Redis
        try:
            val = RedisClient().client.get(key)
            if val:
                # Assuming JSON storage for complex objects
                try:
                    data = json.loads(val)
                except json.JSONDecodeError:
                    data = val

                # Populate local cache
                self._local_cache[key] = data
                return data
        except Exception as e:
            raise InternalError(f"Error getting key {key} from Redis") from e

        return None

    def set(self, key: str, value: Any, ttl: int = 3600):
        logger.debug(f"Setting key: {key} with ttl: {ttl}")
        # Set local
        self._local_cache[key] = value

        # Set Redis
        try:
            if isinstance(value, (dict, list)):
                val_str = json.dumps(value)
            else:
                val_str = str(value)
            RedisClient().client.setex(key, ttl, val_str)
        except Exception as e:
            raise InternalError(f"Error setting key {key} in Redis") from e

    def expel(self, key: str):
        logger.debug(f"Expelling key: {key}")
        if key in self._local_cache:
            del self._local_cache[key]
        try:
            RedisClient().client.delete(key)
        except Exception as e:
            raise InternalError(f"Error deleting key {key} from Redis") from e

    def clear_local(self):
        logger.debug("Clearing local cache")
        self._local_cache.clear()

    def clear_redis(self):
        logger.debug("Clearing Redis cache")
        try:
            RedisClient().client.flushdb()
        except Exception as e:
            raise InternalError("Error flushing Redis db") from e
