import unittest
from unittest.mock import MagicMock, patch

from omni_python_library.clients.openai_client import OpenAIClient
from omni_python_library.utils.errors import BadParameterError, InternalError


class TestOpenAIClient(unittest.TestCase):
    def setUp(self):
        self.client = OpenAIClient()
        self.client._clients = {}
        self.client._base_url_clients = {}

    @patch("omni_python_library.clients.openai_client.OpenAI")
    def test_register_client_success(self, mock_openai):
        # Arrange
        mock_model = MagicMock()
        mock_model.id = "gpt-4"
        mock_openai.return_value.models.list.return_value.data = [mock_model]

        # Act
        self.client.add_client("test_use", "test_api_key", "http://localhost:8080", "gpt-4")

        # Assert
        mock_openai.assert_called_once_with(api_key="test_api_key", base_url="http://localhost:8080")
        self.assertIn("test_use", self.client._clients)
        self.assertEqual(self.client._clients["test_use"][1], "gpt-4")

    @patch("omni_python_library.clients.openai_client.OpenAI")
    def test_register_client_model_not_found(self, mock_openai):
        # Arrange
        mock_model = MagicMock()
        mock_model.id = "gpt-3.5-turbo"
        mock_openai.return_value.models.list.return_value.data = [mock_model]

        # Act & Assert
        with self.assertRaises(BadParameterError) as context:
            self.client.add_client("test_use", "test_api_key", "http://localhost:8080", "gpt-4")
        self.assertIn("Model 'gpt-4' not found", str(context.exception))

    @patch("omni_python_library.clients.openai_client.OpenAI")
    def test_register_client_exception_on_model_verify(self, mock_openai):
        # Arrange
        mock_openai.return_value.models.list.side_effect = Exception("API error")

        # Act & Assert
        with self.assertRaises(InternalError) as context:
            self.client.add_client("test_use", "test_api_key", "http://localhost:8080", "gpt-4")
        self.assertIn("Failed to verify model 'gpt-4'", str(context.exception))


if __name__ == "__main__":
    unittest.main()
