import unittest
from unittest.mock import MagicMock, patch

from omni_python_library import init_omni_library
from omni_python_library.dal.base.arango_operator import ArangoOperator
from omni_python_library.utils import InternalError


class TestGenerateEmbedding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_omni_library()

    @patch("omni_python_library.dal.base.arango_operator.OpenAIClient")
    def test_generate_embedding_success(self, mock_openai_client):
        # Setup mock
        mock_client_instance = MagicMock()
        mock_embedding_response = MagicMock()
        mock_embedding_response.embedding = [0.1, 0.2, 0.3]
        mock_client_instance.embeddings.create.return_value.data = [mock_embedding_response]
        mock_openai_client.return_value.get_client.return_value = (mock_client_instance, "text-embedding-ada-002")

        # Instantiate the operator and call the method
        operator = ArangoOperator()
        result = operator.generate_embedding("test text")

        # Assertions
        self.assertEqual(result, [0.1, 0.2, 0.3])
        mock_openai_client.return_value.get_client.assert_called_once_with("embedding")
        mock_client_instance.embeddings.create.assert_called_once_with(
            input="test text", model="text-embedding-ada-002"
        )

    @patch("omni_python_library.dal.base.arango_operator.OpenAIClient")
    def test_generate_embedding_api_error(self, mock_openai_client):
        # Setup mock to raise an exception
        mock_client_instance = MagicMock()
        mock_client_instance.embeddings.create.side_effect = Exception("API Error")
        mock_openai_client.return_value.get_client.return_value = (mock_client_instance, "text-embedding-ada-002")

        # Instantiate the operator
        operator = ArangoOperator()

        # Call the method and assert it raises the expected exception
        with self.assertRaises(InternalError) as context:
            operator.generate_embedding("test text")

        self.assertEqual(str(context.exception), "Error generating embedding")
        mock_client_instance.embeddings.create.assert_called_once_with(
            input="test text", model="text-embedding-ada-002"
        )


if __name__ == "__main__":
    unittest.main()
