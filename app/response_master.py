import os
import logging
from app.helpers.pinecone_handler import PineconeHandler
from app.prompt_library.prompt_master import PromptMaster


class responseHandler:
    """
    Handles incoming messages, fetches relevant documents from the index,
    and generates prompts for the language model.

    Attributes:
        pinecone_handler (PineconeHandler): Instance of PineconeHandler.
        prompt_master (PromptMaster): Instance of PromptMaster.

    Methods:
        __init__(pinecone_handler, prompt_master):
            Initializes the ResponseHandler class with the PineconeHandler
            and PromptMaster instances.
        get_response(incoming_msg):
            Gets the response based on the incoming message.
    """

    def __init__(self):
        """
        Initializes the ResponseHandler class with the PineconeHandler and PromptMaster instances.
        """
        self.pinecone = PineconeHandler()
        self.prompt_master = PromptMaster("response_master")

    def get_response(self, incoming_msg: str) -> dict:
        """
        1. Check if the response is in the cache
        2. Get the documents from the index
        3. Generate prompt for llm
        4. Return the response
        """
        # Check if the response is in the cache
        response: dict = self.pinecone.check_cache(incoming_msg)
        if response["hit"]:
            return {
                "result": True,
                "type": "response",
                "response": response["response"],
            }

        # Get the documents from the index
        try:
            # Fetch documents
            docs = self.pinecone.pc_search(
                index_name=os.environ["PERSONAL_DOC_INDEX"],
                query=incoming_msg,
                top_k=5,
            )

            # Get Relevant documents
            if not docs or len(docs) == 0:
                return {
                    "result": False,
                    "response": "No documents found",
                }
            docs_text = "\n".join(doc for doc in docs)

            # Generate prompt for llm
            prompt = self.prompt_master.get_prompt(
                "master_response",
                incoming_msg=incoming_msg,
                docs=docs_text,
            )
            return {
                "result": True,
                "type": "prompt",
                "response": prompt,
            }

        except Exception as e:
            logging.error("Error fetching documents: %s", e)
            return {
                "result": False,
                "type": "error",
                "response": "Error fetching documents",
            }
