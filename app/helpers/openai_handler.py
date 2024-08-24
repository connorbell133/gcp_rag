import os
import logging
from openai import OpenAI


class embeddingHandler:
    """
    Embedding handler class to get embeddings for the text.
    Attributes:
        gpt_cli (OpenAI): Instance of OpenAI.
    Methods:
        __init__(): Initializes the embeddingHandler class with the OpenAI instance.
        get_embedding(text: str) -> list[float]:
                Gets the embedding for the text."""

    def __init__(self) -> None:
        self.gpt_cli = OpenAI()

    def get_embedding(self, text: str) -> list[float]:
        """
        Gets the embedding for the text.
        """
        try:
            embedding = self.gpt_cli.embeddings.create(
                input=text, model=os.environ["OPENAI_MODEL"], dimensions=1536
            )
            embedding = embedding.data[0].embedding
            return embedding
        except Exception as e:
            logging.error("Error during get_embedding: %s", e)
            raise e
