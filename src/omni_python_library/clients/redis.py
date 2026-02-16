from typing import Optional

from redis import Redis

from omni_python_library.utils.singleton import Singleton

CACHER = 0
PENDING_UPDATES = 1
MONITORING = 2


class RedisClient(Singleton):
    def init(self, host: str = "localhost", port: int = 6379, password: Optional[str] = None):
        self._host = host
        self._port = int(port)
        self._password = password

        self._clients = {
            CACHER: Redis(host=self._host, port=self._port, db=CACHER, password=self._password, decode_responses=True),
            PENDING_UPDATES: Redis(
                host=self._host, port=self._port, db=PENDING_UPDATES, password=self._password, decode_responses=True
            ),
            MONITORING: Redis(
                host=self._host, port=self._port, db=MONITORING, password=self._password, decode_responses=True
            ),
        }

    @property
    def client(self) -> Redis:
        return self._clients[CACHER]

    @property
    def pending_updates_client(self) -> Redis:
        return self._clients[PENDING_UPDATES]

    @property
    def monitoring_client(self) -> Redis:
        return self._clients[MONITORING]

    def get_client(self, db: int = CACHER) -> Redis:
        return self._clients[db]
