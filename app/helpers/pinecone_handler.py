"""
File for handling the Pinecone API for indexing and searching documents.
class PineconeHandler:
    Handles the Pinecone API for indexing and searching documents.

    Attributes:
        pc (Pinecone): Instance of Pinecone.
        embedding_handler (embeddingHandler): Instance of embeddingHandler.

    Methods:
        __init__():
            Initializes the PineconeHandler class with the Pinecone and embeddingHandler instances.
        _get_index(index_name):
            Gets the index based on the index name.
        pc_upsert(index_name, text, namespace, metadata):
            Upserts the document into the index.
        pc_search(index_name, query, top_k):
            Searches the index for the query.
        check_cache(incoming_msg):
            Checks if the response is in the cache.
"""

import logging
from os import environ as en
import random

from pinecone import Pinecone, Index

from app.helpers.openai_handler import embeddingHandler


class PineconeHandler:
    """
    Handles the Pinecone API for indexing and searching documents.

    Attributes:
        pc (Pinecone): Instance of Pinecone.
        embedding_handler (embeddingHandler): Instance of embeddingHandler.

    Methods:
        __init__():
            Initializes the PineconeHandler class with the Pinecone and embeddingHandler instances.
        _get_index(index_name):
            Gets the index based on the index name.
        pc_upsert(index_name, text, namespace, metadata):
            Upserts the document into the index.
        pc_search(index_name, query, top_k):
            Searches the index for the query.
        check_cache(incoming_msg):
            Checks if the response is in the cache.
    """

    def __init__(self):
        """
        Initializes the PineconeHandler class with the Pinecone and embeddingHandler instances.
        """
        self.pc = Pinecone(api_key=en.get("PINECONE_API_KEY"))
        self.embedding_handler = embeddingHandler()

    def _get_index(self, index_name: str) -> Index:
        """
        Gets the index based on the index name.
        """
        try:
            return self.pc.Index(index_name)
        except Exception as e:
            logging.error("Error during index search: %s", e)
            raise Exception("Error during index search %s", e)

    def pc_upsert(
        self, index_name: str, text: str, namespace: str = "", metadata=None
    ) -> bool:
        """
        Upserts the document into the index.
        """

        index = self._get_index(index_name)
        if index is None:
            logging.error("Index not found")
            return False

        # Embed the text
        embedding: list[float] = self.embedding_handler.get_embedding(text)
        if not embedding:
            logging.error("Error getting embedding")
            return False

        try:
            chunk = {
                "id": str(random.randint(100000, 999999)),
                "values": embedding,
                "metadata": metadata,
            }

            index.upsert(vectors=[chunk], namespace=namespace)
            logging.info("Document %s upserted successfully to %s", text, index_name)
            return True

        except Exception as e:
            print(f"Error during upsert: {e}")
            return False

    def pc_search(self, index_name: str, query: str, top_k: int = 5) -> list:
        """
        Searches the index for the query.
        """
        index = self._get_index(index_name)
        if index is None:
            logging.error("Index not found")
            raise Exception("Index not found")

        # Embed the text
        embedding: list[float] = self.embedding_handler.get_embedding(query)
        if not embedding:
            logging.error("Error getting embedding")
            raise Exception("Error getting embedding")

        try:
            search_resp = index.query(
                vector=embedding,
                top_k=top_k,
                include_values=False,
                include_metadata=True,
            )
            logging.info(search_resp)
            for match in search_resp.matches:
                logging.info(match.metadata["text"])
            # If response found in cache with a score above the threshold
            relevant_responses: list = [
                match.metadata["text"]
                for match in search_resp.matches
                if match.score > 0.22
            ]
            logging.info(len(relevant_responses))
            if relevant_responses:
                logging.info("Response found in cache")
                return relevant_responses
            else:
                logging.info("No response found in cache")
                return relevant_responses
        except Exception as e:
            raise Exception("Error during search query, %s", e)

    def check_cache(self, incoming_msg: str) -> dict:
        """
        Check if the response is in the cache
        """

        # Search the index for the incoming message
        # chat_cache: list = self.pc_search(index_name="", query=incoming_msg, top_k=1)
        index = self._get_index(en["CHAT_CACHE_INDEX"])
        if index is None:
            logging.error("Index not found")
            raise Exception("Index not found")
        # Embed the text
        embedding: list[float] = self.embedding_handler.get_embedding(incoming_msg)
        if not embedding:
            logging.error("Error getting embedding")
            raise Exception("Error getting embedding")

        try:
            search_resp = index.query(
                vector=embedding,
                top_k=1,
                include_values=False,
                include_metadata=True,
            )
            logging.info(search_resp)

            # If response found in cache with a score above the threshold
            if search_resp.matches[0].score > 0.6:
                logging.info("Response found in cache")
                return {
                    "hit": True,
                    "response": search_resp.matches[0].metadata["response"],
                }
            else:
                logging.info("No response found in cache")
                return {
                    "hit": False,
                    "response": "No response found",
                }

        except Exception as e:
            raise Exception("Error during search query, %s", e)
