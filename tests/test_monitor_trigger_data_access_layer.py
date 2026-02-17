import unittest
from unittest.mock import MagicMock, patch

from omni_python_library.dal.monitor_trigger_data_access_layer import MonitorTriggerDataAccessLayer
from omni_python_library.models.monitor_trigger import MonitorTrigger


class TestMonitorTriggerDataAccessLayer(unittest.TestCase):
    def setUp(self):
        self.dal = MonitorTriggerDataAccessLayer()
        self.mock_redis_client = MagicMock()
        self.mock_pipeline = MagicMock()
        self.mock_redis_client.pipeline.return_value.__enter__.return_value = self.mock_pipeline

        # Patch RedisClient to return our mock
        self.redis_client_patcher = patch("omni_python_library.dal.monitor_trigger_data_access_layer.RedisClient")
        self.mock_redis_client_constructor = self.redis_client_patcher.start()
        self.mock_redis_client_constructor.return_value.monitoring_client = self.mock_redis_client

    def tearDown(self):
        self.redis_client_patcher.stop()

    def test_create_monitor_trigger(self):
        trigger = MonitorTrigger(user_id="user1", language="en")
        self.dal.create_monitor_trigger(trigger)

        self.mock_pipeline.sadd.assert_called_once_with("monitor_triggers", "user1")
        self.mock_pipeline.hset.assert_called_once_with("monitor_trigger:user1", mapping=trigger.model_dump())
        self.mock_pipeline.execute.assert_called_once()

    def test_delete_monitor_trigger(self):
        user_id = "user1"
        self.dal.delete_monitor_trigger(user_id)

        self.mock_pipeline.srem.assert_called_once_with("monitor_triggers", user_id)
        self.mock_pipeline.delete.assert_called_once_with("monitor_trigger:user1")
        self.mock_pipeline.execute.assert_called_once()

    def test_get_monitor_trigger_found(self):
        user_id = "user1"
        trigger_data = {"user_id": user_id, "language": "en"}
        encoded_data = {k.encode("utf-8"): v.encode("utf-8") for k, v in trigger_data.items()}
        self.mock_redis_client.hgetall.return_value = encoded_data

        trigger = self.dal.get_monitor_trigger(user_id)

        self.assertIsNotNone(trigger)
        self.assertEqual(trigger.user_id, user_id)
        self.assertEqual(trigger.language, "en")
        self.mock_redis_client.hgetall.assert_called_once_with("monitor_trigger:user1")

    def test_get_monitor_trigger_not_found(self):
        user_id = "user1"
        self.mock_redis_client.hgetall.return_value = None

        trigger = self.dal.get_monitor_trigger(user_id)

        self.assertIsNone(trigger)
        self.mock_redis_client.hgetall.assert_called_once_with("monitor_trigger:user1")

    def test_list_monitor_triggers_empty(self):
        self.mock_redis_client.smembers.return_value = []

        triggers = self.dal.list_monitor_triggers()

        self.assertEqual(triggers, [])
        self.mock_redis_client.smembers.assert_called_once_with("monitor_triggers")

    def test_list_monitor_triggers_with_data(self):
        user_ids = [b"user1", b"user2"]
        trigger_data1 = {"user_id": "user1", "language": "en"}
        trigger_data2 = {"user_id": "user2", "language": "fr"}
        encoded_data1 = {k.encode("utf-8"): v.encode("utf-8") for k, v in trigger_data1.items()}
        encoded_data2 = {k.encode("utf-8"): v.encode("utf-8") for k, v in trigger_data2.items()}

        self.mock_redis_client.smembers.return_value = user_ids
        self.mock_pipeline.execute.return_value = [encoded_data1, encoded_data2]

        triggers = self.dal.list_monitor_triggers()

        self.assertEqual(len(triggers), 2)
        self.assertEqual(triggers[0].user_id, "user1")
        self.assertEqual(triggers[1].user_id, "user2")
        self.mock_redis_client.smembers.assert_called_once_with("monitor_triggers")
        self.assertEqual(self.mock_pipeline.hgetall.call_count, 2)
