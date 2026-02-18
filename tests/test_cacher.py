import unittest

from omni_python_library import init_omni_library
from omni_python_library.dal.base.cacher import Cacher


class TestCacher(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_omni_library()

    def setUp(self):
        self.cacher = Cacher()
        self.cacher.init()
        self.cacher.clear_redis()
        self.cacher.clear_local()

    def test_set_get_string(self):
        key = "test_string"
        value = "hello world"
        self.cacher.set(key, value)
        retrieved_value = self.cacher.get(key)
        self.assertEqual(retrieved_value, value)

    def test_set_get_int(self):
        key = "test_int"
        value = 123
        self.cacher.set(key, value)
        retrieved_value = self.cacher.get(key)
        self.assertEqual(retrieved_value, value)

    def test_set_get_list(self):
        key = "test_list"
        value = [1, "two", 3.0]
        self.cacher.set(key, value)
        retrieved_value = self.cacher.get(key)
        self.assertEqual(retrieved_value, value)

    def test_set_get_dict(self):
        key = "test_dict"
        value = {"a": 1, "b": "two", "c": [1, 2, 3]}
        self.cacher.set(key, value)
        retrieved_value = self.cacher.get(key)
        self.assertEqual(retrieved_value, value)

    def test_expel(self):
        key = "test_expel"
        value = "some value"
        self.cacher.set(key, value)
        self.assertIsNotNone(self.cacher.get(key))
        self.cacher.expel(key)
        self.assertIsNone(self.cacher.get(key))

    def test_clear_local(self):
        key = "test_clear_local"
        value = "some value"
        self.cacher.set(key, value)
        # Verify it's in the local cache
        self.assertIsNotNone(self.cacher._local_caches[0].get(key))
        self.cacher.clear_local()
        self.assertIsNone(self.cacher._local_caches[0].get(key))
        # It should still be in Redis
        self.assertIsNotNone(self.cacher.get(key))

    def test_clear_redis(self):
        key = "test_clear_redis"
        value = "some value"
        self.cacher.set(key, value)
        self.assertIsNotNone(self.cacher.get(key))
        self.cacher.clear_redis()
        self.cacher.clear_local()  # Clear local cache to ensure we fetch from Redis
        self.assertIsNone(self.cacher.get(key))
