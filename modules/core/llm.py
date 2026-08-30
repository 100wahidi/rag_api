from mistralai.client import Mistral
import asyncio


class Llm:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = None  # Default model
        self.operational_llms = ["mistral-7b-instruct-v0.1","mistral-medium-latest","mistral-7b-instruct-v0.2"]  # List of operational LLMs

    def get_llm_client(self):
        """
        Returns an instance of the LLM client based on the provided API key.
        """
        return Mistral(api_key=self.api_key)

    def get_avalable_models(self):
        """
        Returns a list of available models from the LLM client.
        """
        client = self.get_llm_client()
        models = [row.id for row in client.models.list().data]
        return models
    
    def handlel_llm(self):
        available_models = self.get_avalable_models()
        if self.model not in available_models:
            self.model = None
        for model in self.operational_llms:
            if model in available_models:
                self.model = model
                return self.model
        raise ValueError("No operational LLM model is available.")
