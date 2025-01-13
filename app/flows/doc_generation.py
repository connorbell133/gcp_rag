from typing import List, Dict, Any
from app.flows.BaseFlow import BaseFlow
from app.universal_data import (
    validate_and_store_doc_data,
    get_subtask_state,
)
import logging

logging.basicConfig(level=logging.DEBUG)


# === SUBFLOWS ===
class IntroductionFlow(BaseFlow):
    """
    This subflow is responsible for collecting the first piece of data required for the document.

    It is the first step in the document creation process.

    Subflow Steps:
    - Check if all required data has been collected
    - Collect the first piece of data
    """

    def __init__(
        self,
        doc_metadata: List[Dict[str, Any]],
        index: str,
    ):
        self.doc_metadata = doc_metadata
        self.index = index

    def handle_step(self, user_message: str, conversation_id: str):
        questions = self.doc_metadata[:3]
        logging.info("Questions: %s", questions)
        for meta_config in questions:
            key = meta_config["key"]
            logging.info("Intro Key: %s", key)
            doc_state = get_subtask_state(conversation_id, "doc_creation_flow")
            logging.info("Doc State: %s", doc_state)
            if key not in doc_state["data"]["subtask_data"]:
                logging.info("Key not in subtask data")
                logging.info("handle_doc_state: %s", doc_state)

                result = validate_and_store_doc_data(
                    doc_state["data"],
                    user_message,
                    meta_config,
                    self.index,
                )
                if result["result"] == "stored":
                    # Stored successfully, move on to next item
                    continue
                elif result["result"] in ("prompt", "error"):
                    return {"message": result["message"], "done": "no"}

        # After you finish storing all required keys for this subflow,
        # check if you are complete:
        if self.is_complete(conversation_id):
            return {"message": "Introduction done!", "done": "yes"}
        else:
            return {"message": "Still missing data for IntroductionFlow.", "done": "no"}

    def is_complete(self, conversation_id: str) -> bool:
        doc_state = get_subtask_state(conversation_id, "doc_creation_flow")
        # For the "introduction," we want the first 3 keys (name, favorite_color, email)
        return len(doc_state["data"]["subtask_data"]) >= 3


class MiddleFlow(BaseFlow):
    """
    This subflow is responsible for collecting the second piece of data required for the document.

    It is the second step in the document creation process.

    Subflow Steps:
    - Check if all required data has been collected
    - Collect the second piece of data
    """

    def __init__(
        self,
        doc_metadata: List[Dict[str, Any]],
        index: str,
    ):
        self.doc_metadata = doc_metadata
        self.index = index

    def handle_step(self, user_message: str, conversation_id: str):
        questions = self.doc_metadata[3:4]  # Only one question in this flow
        logging.info("Questions: %s", questions)

        for meta_config in questions:
            key = meta_config["key"]
            logging.info("Middle Key: %s", key)

            doc_state = get_subtask_state(conversation_id, "doc_creation_flow")
            logging.info("Doc State: %s", doc_state)

            if key not in doc_state["data"]["subtask_data"]:
                logging.info("Key not in subtask data")
                logging.info("handle_doc_state: %s", doc_state)
                result = validate_and_store_doc_data(
                    doc_state["data"],
                    user_message,
                    meta_config,
                    self.index,
                )
                if result["result"] == "stored":
                    continue
                elif result["result"] in ("prompt", "error"):
                    return {"message": result["message"], "done": "no"}

        if self.is_complete(conversation_id):
            return {"message": "Middle done!", "done": "yes"}
        else:
            return {"message": "Still missing data for MiddleFlow.", "done": "no"}

    def is_complete(self, conversation_id: str) -> bool:
        doc_state = get_subtask_state(conversation_id, "doc_creation_flow")
        # For the "introduction," we want the first 3 keys (name, favorite_color, email)
        return len(doc_state["data"]["subtask_data"]) >= 4


class EndFlow(BaseFlow):
    """
    This subflow is responsible for collecting the last piece of data required for the document.

    It is the third step in the document creation process.

    Subflow Steps:
    - Check if all required data has been collected
    - Collect the last piece of data
    """

    def __init__(
        self,
        doc_metadata: List[Dict[str, Any]],
        index: str,
    ):
        self.doc_metadata = doc_metadata
        self.index = index

    def handle_step(self, user_message: str, conversation_id: str):
        questions = self.doc_metadata[4:]
        for meta_config in questions:
            key = meta_config["key"]
            logging.info("Intro Key: %s", key)
            doc_state = get_subtask_state(conversation_id, "doc_creation_flow")
            logging.info("Doc State: %s", doc_state)
            if key not in doc_state["data"]["subtask_data"]:
                logging.info("Key not in subtask data")
                logging.info("handle_doc_state: %s", doc_state)
                result = validate_and_store_doc_data(
                    doc_state["data"],
                    user_message,
                    meta_config,
                    self.index,
                )
                if result["result"] == "stored":
                    # Stored successfully, move on to next item
                    continue
                elif result["result"] in ("prompt", "error"):
                    return {"message": result["message"], "done": "no"}

        if self.is_complete(conversation_id):
            return {"message": "Middle done!", "done": "yes"}
        else:
            return {"message": "Still missing data for EndFlow.", "done": "no"}

    def is_complete(self, conversation_id: str) -> bool:
        doc_state = get_subtask_state(conversation_id, "doc_creation_flow")
        # For the "introduction," we want the first 3 keys (name, favorite_color, email)
        return len(doc_state["data"]["subtask_data"]) >= 5


class GenerateDocument(BaseFlow):
    """
    This subflow is responsible for generating the document based on the collected  data.

    It is the final step in the document creation process.

    Subflow Steps:
    - Check if all required data has been collected
    - Generate the document
    """

    def __init__(
        self,
        doc_metadata: List[Dict[str, Any]],
        index: str,
    ):
        self.doc_metadata = doc_metadata
        self.index = index

    def handle_step(self, user_message: str, conversation_id: str):
        doc_state = get_subtask_state(conversation_id, "doc_creation_flow")
        # set step complete
        doc_state["data"]["subtask_completed"] = True

        if self.is_complete(conversation_id):

            return self.generate_document(doc_state["data"]["subtask_data"])
        else:
            return {"message": "Still missing data for EndFlow.", "done": "no"}

    def is_complete(self, conversation_id: str) -> bool:

        doc_state = get_subtask_state(conversation_id, "doc_creation_flow")
        return doc_state["data"]["subtask_completed"]

    def generate_document(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate the document based on the collected data.

        The document will be a string that includes all the collected data.

        Example:
        === GENERATED DOCUMENT ===
        Name: John Doe
        Favorite Color: Blue
        Email:
        Hobby: Reading

        === END OF DOCUMENT ===

        """
        doc = (
            "=== GENERATED DOCUMENT ===\n"
            f"Name: {doc_data.get('name', '')}\n"
            f"Favorite Color: {doc_data.get('favorite_color', '')}\n"
            f"Email: {doc_data.get('email', '')}\n"
            f"Hobby: {doc_data.get('hobby', '')}\n"
            f"Country: {doc_data.get('country', '')}\n"
            "=== END OF DOCUMENT ===\n"
        )
        return {
            "message": doc,
            "done": "yes",
        }


# === MAIN FLOW ===
class DocumentCreationFlow(BaseFlow):
    """
    This flow is responsible for guiding the user through the process of creating a document.

    The flow consists of 4 subflows:
    - IntroductionFlow
    - MiddleFlow
    - EndFlow
    - Generate_Document

    Each subflow is responsible for collecting a subset of the required data.
    """

    def __init__(self):
        self.doc_metadata = [
            {
                "key": "name",
                "prompt": "What's your name?",
                "response_type": "string",
            },
            {
                "key": "favorite_color",
                "prompt": "What's your favorite color? (red, blue, green)",
                "response_type": "list",
                "response_list": ["red", "blue", "green"],
            },
            {
                "key": "email",
                "prompt": "Please provide your email for the document.",
                "response_type": "regex",
                "response_regex": r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
            },
            {
                "key": "hobby",
                "prompt": "What's your favorite hobby?",
                "response_type": "string",
            },
            {
                "key": "country",
                "prompt": "Which country do you live in?",
                "response_type": "string",
            },
        ]
        self.subflows = {
            "introduction": IntroductionFlow(self.doc_metadata, "doc_creation_flow"),
            "middle": MiddleFlow(self.doc_metadata, "doc_creation_flow"),
            "end": EndFlow(
                self.doc_metadata,
                "doc_creation_flow",
            ),
            "generate": GenerateDocument(
                self.doc_metadata,
                "doc_creation_flow",
            ),
        }

    # ===== BaseFlow Methods =====
    def is_complete(self, conversation_id: str) -> bool:

        # Access subtask_data in conversation_state
        doc_state = get_subtask_state(conversation_id, "doc_creation_flow")
        return doc_state["data"]["subtask_completed"]

    def handle_step(self, user_message: str, conversation_id: str):

        logging.info("Handling step for document creation flow")
        subtask_state = get_subtask_state(conversation_id, "doc_creation_flow")
        logging.info("Subtask state: %s", subtask_state)
        current_subflow = subtask_state["data"].get("current_subflow") or "introduction"

        # Call the active subflow
        logging.info("Current subflow: %s", current_subflow)
        logging.info("Doc state: %s", subtask_state)
        logging.info("User message: %s", user_message)
        logging.info("Subflows: %s", self.subflows)
        flow_result = self.subflows[current_subflow].handle_step(
            user_message, conversation_id
        )
        if flow_result["done"] == "yes":
            logging.info("Subflow done")
            # Determine the next subflow
            subflow_keys = list(self.subflows.keys())
            current_index = subflow_keys.index(current_subflow)
            if current_index < len(subflow_keys) - 1:
                logging.info("Moving to next subflow")
                subtask_state["data"]["current_subflow"] = subflow_keys[
                    current_index + 1
                ]
            else:
                subtask_state["data"]["subtask_completed"] = True
                logging.info("All subflows complete")
        return flow_result
