import json
from typing import Any, Optional

from cachetools import LRUCache

from omni_python_library.clients.redis import RedisClient
from omni_python_library.utils.singleton import Singleton


class Cacher(Singleton):
    def init(self):
        super().init()
        self._local_cache: LRUCache = LRUCache(maxsize=1000)
        self._redis_client = RedisClient().client

    def get(self, key: str) -> Optional[Any]:
        # Check local cache first
        if key in self._local_cache:
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
        except Exception:
            # Fallback or log error
            pass

        return None

    def set(self, key: str, value: Any, ttl: int = 3600):
        # Set local
        self._local_cache[key] = value

        # Set Redis
        try:
            if isinstance(value, (dict, list)):
                val_str = json.dumps(value)
            else:
                val_str = str(value)
            RedisClient().client.setex(key, ttl, val_str)
        except Exception:
            pass

    def expel(self, key: str):
        if key in self._local_cache:
            del self._local_cache[key]
        try:
            RedisClient().client.delete(key)
        except Exception:
            pass

    def clear_local(self):
        self._local_cache.clear()

    def clear_redis(self):
        try:
            RedisClient().client.flushdb()
        except Exception:
            pass
