import logging
from typing import List, Optional

from omni_python_library.clients import RedisClient
from omni_python_library.models import MonitorTrigger

logger = logging.getLogger(__name__)


class MonitorTriggerDataAccessLayer:
    MONITOR_TRIGGERS_SET_KEY = "monitor_triggers"

    def _get_trigger_key(self, user_id: str) -> str:
        return f"monitor_trigger:{user_id}"

    def create_monitor_trigger(self, trigger: MonitorTrigger):
        with RedisClient().monitoring_client.pipeline() as pipe:
            pipe.sadd(self.MONITOR_TRIGGERS_SET_KEY, trigger.user_id)
            pipe.hset(self._get_trigger_key(trigger.user_id), mapping=trigger.model_dump())
            pipe.execute()

    def delete_monitor_trigger(self, user_id: str):
        with RedisClient().monitoring_client.pipeline() as pipe:
            pipe.srem(self.MONITOR_TRIGGERS_SET_KEY, user_id)
            pipe.delete(self._get_trigger_key(user_id))
            pipe.execute()

    def list_monitor_triggers(self) -> List[MonitorTrigger]:
        user_ids = RedisClient().monitoring_client.smembers(self.MONITOR_TRIGGERS_SET_KEY)
        if not user_ids:
            return []

        with RedisClient().monitoring_client.pipeline() as pipe:
            for user_id in user_ids:
                pipe.hgetall(self._get_trigger_key(user_id))
            results = pipe.execute()

        triggers = []
        for data in results:
            if data:
                triggers.append(MonitorTrigger(**data))
        return triggers

    def get_monitor_trigger(self, user_id: str) -> Optional[MonitorTrigger]:
        data = RedisClient().monitoring_client.hgetall(self._get_trigger_key(user_id))
        if not data:
            return None
        return MonitorTrigger(**data)
