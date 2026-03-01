import os
import unittest
from unittest.mock import mock_open, patch

from omni_python_library.utils.config import ConfigRegistry
from omni_python_library.utils.singleton import Singleton


class TestConfigRegistry(unittest.TestCase):
    def setUp(self):
        # Reset singleton instance before each test
        Singleton._instances = {}

    def test_singleton_behavior(self):
        instance1 = ConfigRegistry()
        instance2 = ConfigRegistry()
        self.assertIs(instance1, instance2)

    @patch.dict(os.environ, {"IS_LOCAL": "true", "MY_KEY": "my_value"})
    def test_get_local_stage_from_env(self):
        registry = ConfigRegistry()
        registry.init(root_path="/fake/path")
        self.assertEqual(registry.get("MY_KEY"), "my_value")

    @patch.dict(os.environ, {"IS_LOCAL": "true"})
    def test_get_local_stage_missing_key(self):
        registry = ConfigRegistry()
        registry.init(root_path="/fake/path")
        # Should return empty string and log a warning, but we can't easily test the log here
        self.assertEqual(registry.get("MISSING_KEY"), "")

    @patch.dict(os.environ, {"IS_LOCAL": "false", "MY_KEY": "prod_value"})
    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data="file_value")
    def test_get_prod_stage_from_file(self, mock_file, mock_exists):
        registry = ConfigRegistry()
        registry.init(root_path="/fake/path")
        value = registry.get("MY_KEY")

        self.assertEqual(value, "file_value")
        mock_exists.assert_called_once_with("/fake/path/MY_KEY")
        mock_file.assert_called_once_with("/fake/path/MY_KEY", "r")

    @patch.dict(os.environ, {"IS_LOCAL": "false", "MY_KEY": "env_value"})
    @patch("os.path.exists", return_value=False)
    def test_get_prod_stage_fallback_to_env(self, mock_exists):
        registry = ConfigRegistry()
        registry.init(root_path="/fake/path")
        self.assertEqual(registry.get("MY_KEY"), "env_value")

    @patch.dict(os.environ, {"IS_LOCAL": "false"})
    @patch("os.path.exists", return_value=False)
    def test_get_prod_stage_raises_exception(self, mock_exists):
        # Clear MY_KEY if it exists from a previous test's patch
        if "MY_KEY" in os.environ:
            del os.environ["MY_KEY"]

        registry = ConfigRegistry()
        registry.init(root_path="/fake/path")
        with self.assertRaisesRegex(Exception, "Config key MISSING_KEY not found in both file and env var"):
            registry.get("MISSING_KEY")


if __name__ == "__main__":
    unittest.main()
