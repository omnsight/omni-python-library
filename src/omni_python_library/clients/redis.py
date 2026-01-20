from typing import Optional

import redis

from omni_python_library.utils.singleton import Singleton


class RedisClient(Singleton):
    def init(self, host: str = "localhost", port: int = 6379, db: int = 0, password: Optional[str] = None):
        self._host = host
        self._port = int(port)
        self._db = int(db)
        self._password = password

        self._client = redis.Redis(
            host=self._host, port=self._port, db=self._db, password=self._password, decode_responses=True
        )

    @property
    def client(self):
        return self._client
