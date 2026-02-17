import unittest

from omni_python_library import init_omni_library
from omni_python_library.clients import RedisClient
from omni_python_library.dal.monitor_trigger_data_access_layer import MonitorTriggerDataAccessLayer
from omni_python_library.models.monitor_trigger import MonitorTrigger


class TestMonitorTriggerDataAccessLayer(unittest.TestCase):
    def setUp(self):
        init_omni_library()
        self.dal = MonitorTriggerDataAccessLayer()
        self.redis_client = RedisClient().monitoring_client

    def tearDown(self):
        self.redis_client.flushdb()

    def test_create_monitor_trigger(self):
        trigger = MonitorTrigger(user_id="user1", language="en")
        self.dal.create_monitor_trigger(trigger)

        # Verify data is in Redis
        self.assertTrue(self.redis_client.sismember("monitor_triggers", "user1"))
        stored_trigger = self.redis_client.hgetall("monitor_trigger:user1")
        self.assertEqual(stored_trigger["user_id"], "user1")
        self.assertEqual(stored_trigger["language"], "en")

    def test_delete_monitor_trigger(self):
        user_id = "user1"
        trigger = MonitorTrigger(user_id=user_id, language="en")
        self.dal.create_monitor_trigger(trigger)  # Pre-populate data

        self.dal.delete_monitor_trigger(user_id)

        # Verify data is deleted from Redis
        self.assertFalse(self.redis_client.sismember("monitor_triggers", user_id))
        self.assertFalse(self.redis_client.exists(f"monitor_trigger:{user_id}"))

    def test_get_monitor_trigger_found(self):
        user_id = "user1"
        trigger_data = {"user_id": user_id, "language": "en"}
        self.redis_client.hset(f"monitor_trigger:{user_id}", mapping=trigger_data)

        trigger = self.dal.get_monitor_trigger(user_id)

        self.assertIsNotNone(trigger)
        self.assertEqual(trigger.user_id, user_id)
        self.assertEqual(trigger.language, "en")

    def test_get_monitor_trigger_not_found(self):
        user_id = "user1"
        trigger = self.dal.get_monitor_trigger(user_id)

        self.assertIsNone(trigger)

    def test_list_monitor_triggers_empty(self):
        triggers = self.dal.list_monitor_triggers()

        self.assertEqual(triggers, [])

    def test_list_monitor_triggers_with_data(self):
        trigger1 = MonitorTrigger(user_id="user1", language="en")
        trigger2 = MonitorTrigger(user_id="user2", language="fr")
        self.dal.create_monitor_trigger(trigger1)
        self.dal.create_monitor_trigger(trigger2)

        triggers = self.dal.list_monitor_triggers()

        self.assertEqual(len(triggers), 2)
        # The order is not guaranteed, so we check for presence
        user_ids = {t.user_id for t in triggers}
        self.assertIn("user1", user_ids)
        self.assertIn("user2", user_ids)
