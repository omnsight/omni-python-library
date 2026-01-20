from typing import Dict, Optional, Tuple

from openai import OpenAI

from omni_python_library.utils.singleton import Singleton


class OpenAIClient(Singleton):
    def init(self):
        self._clients: Dict[str, Tuple[OpenAI, str]] = {}
        self._base_url_clients: Dict[Optional[str], OpenAI] = {}

    def add_client(
        self,
        model_use: str,
        api_key: str,
        base_url: Optional[str] = None,
        model: str = "gpt-4o",
    ) -> None:
        """
        Registers an OpenAI client for a specific model usage.
        """
        if base_url in self._base_url_clients:
            client = self._base_url_clients[base_url]
        else:
            client = OpenAI(api_key=api_key, base_url=base_url)
            self._base_url_clients[base_url] = client

        # Verify model exists
        try:
            available_models = [m.id for m in client.models.list().data]
            if model not in available_models:
                raise ValueError(f"Model '{model}' not found. Available models: {available_models}")
        except Exception as e:
            raise ValueError(f"Failed to verify model '{model}': {str(e)}")

        self._clients[model_use] = (client, model)

    def get_client(self, model_use: str) -> Optional[Tuple[OpenAI, str]]:
        """
        Retrieves the OpenAI client for the specified usage.
        """
        if model_use in self._clients:
            return (self._clients[model_use][0], self._clients[model_use][1])
        return None
