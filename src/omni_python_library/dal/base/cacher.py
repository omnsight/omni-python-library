import json
import logging
from typing import Any, Dict, Optional

from cachetools import TTLCache

from omni_python_library.clients.redis import CACHER, MONITORING, PENDING_UPDATES, RedisClient
from omni_python_library.utils import InternalError, Singleton

logger = logging.getLogger(__name__)


class Cacher(Singleton):
    def init(self, expiration_seconds: int = 5):
        super().init()
        self._local_caches: Dict[int, TTLCache] = {
            db: TTLCache(maxsize=1000, ttl=expiration_seconds) for db in [CACHER, PENDING_UPDATES, MONITORING]
        }

    def get(self, key: str, db: int = 0) -> Optional[Any]:
        # Check local cache first
        local_cache = self._local_caches.get(db)
        if local_cache and key in local_cache:
            logger.debug(f"Key {key} found in local cache for db {db}")
            return local_cache[key]

        # Check Redis
        try:
            val = RedisClient().get_client(db).get(key)
            if val:
                # Assuming JSON storage for complex objects
                try:
                    data = json.loads(val)
                except json.JSONDecodeError:
                    data = val

                # Populate local cache
                if local_cache is not None:
                    local_cache[key] = data
                return data
        except Exception as e:
            raise InternalError(f"Error getting key {key} from Redis") from e

        return None

    def set(self, key: str, value: Any, db: int = 0, ttl: int = 3600):
        logger.debug(f"Setting key: {key} with ttl: {ttl} in db {db}")
        # Set local
        local_cache = self._local_caches.get(db)
        if local_cache is not None:
            local_cache[key] = value

        # Set Redis
        try:
            if isinstance(value, (dict, list)):
                val_str = json.dumps(value)
            else:
                val_str = str(value)
            RedisClient().get_client(db).setex(key, ttl, val_str)
        except Exception as e:
            raise InternalError(f"Error setting key {key} in Redis") from e

    def expel(self, key: str, db: int = 0):
        logger.debug(f"Expelling key: {key} from db {db}")
        local_cache = self._local_caches.get(db)
        if local_cache and key in local_cache:
            del local_cache[key]
        try:
            RedisClient().get_client(db).delete(key)
        except Exception as e:
            raise InternalError(f"Error deleting key {key} from Redis") from e

    def clear_local(self, db: Optional[int] = None):
        if db is not None:
            local_cache = self._local_caches.get(db)
            if local_cache:
                logger.debug(f"Clearing local cache for db {db}")
                local_cache.clear()
        else:
            logger.debug("Clearing all local caches")
            for local_cache in self._local_caches.values():
                local_cache.clear()

    def clear_redis(self, db: int = 0):
        logger.debug(f"Clearing Redis cache for db {db}")
        try:
            RedisClient().get_client(db).flushdb()
        except Exception as e:
            raise InternalError(f"Error flushing Redis db {db}") from e
