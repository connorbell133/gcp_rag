from typing import List, Dict, Any
import re
from app.flows.BaseFlow import BaseFlow
from app.universal_data import convo_state_handler


class IntroductionFlow(BaseFlow):
    def handle_step(self, user_message: str, conversation_id: str):
        # ...subflow logic...
        return {"message": "Introduction done!", "done": "no"}

    def is_complete(self, conversation_id: str) -> bool:
        # ...check completion...
        return False


class DocumentCreationFlow(BaseFlow):
    def __init__(self, doc_metadata: List[Dict[str, Any]]):
        self.doc_metadata = doc_metadata
        self.

    # ===== BaseFlow Methods =====
    def is_complete(self, conversation_id: str) -> bool:

        # Access subtask_data in conversation_state
        doc_state = self.get_doc_state(conversation_id)
        return doc_state["doc_data_completed"]

    def handle_step(self, user_message: str, conversation_id: str) -> Dict[str, Any]:
        """
        Orchestrates question prompts/validation for document creation.
        """
        doc_state = self.get_doc_state(conversation_id)

        # If doc_data_completed, short-circuit
        if doc_state["doc_data_completed"]:
            return {
                "message": "Document subtask is already completed. Here is your document:\n\n"
                f"{self.generate_document(doc_state['doc_data'])}",
                "done": "yes",
            }

        # Attempt to fill in missing keys
        for meta_config in self.doc_metadata:
            key = meta_config["key"]
            if key not in doc_state["doc_data"]:
                # Attempt to validate/store user_message for this key
                result = self.validate_and_store_doc_data(
                    doc_state, user_message, meta_config
                )
                if result["result"] == "stored":
                    # Stored successfully, move on to next item
                    continue
                elif result["result"] in ("prompt", "error"):
                    # Return prompt/error immediately
                    return {"message": result["message"], "done": "no"}

        # If we reach here, all questions answered
        doc_state["doc_data_completed"] = True
        doc_text = self.generate_document(doc_state["doc_data"])
        return {
            "message": f"All questions answered! Here is your document:\n\n{doc_text}",
            "done": "yes",
        }

    # ===== Helper Methods =====
    def get_doc_state(self, conversation_id) -> Dict[str, Any]:
        """
        Retrieve or create the doc_state from conversation_state.
        """
        subtask_data = convo_state_handler[conversation_id]["subtask_data"].get(
            "document_creation"
        )
        if not subtask_data:
            # Initialize
            convo_state_handler[conversation_id]["subtask_data"][
                "document_creation"
            ] = {
                "status": "in_progress",
                "data": {
                    "doc_data": {},
                    "doc_data_completed": False,
                    "last_message_prompt": "",
                },
            }
            subtask_data = convo_state_handler[conversation_id]["subtask_data"][
                "document_creation"
            ]
        return subtask_data["data"]

    def validate_and_store_doc_data(
        self, doc_state: Dict[str, Any], user_message: str, meta_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        key = meta_config["key"]
        last_prompt = doc_state["last_message_prompt"]
        response_type = meta_config.get("response_type", "string")

        if last_prompt == key:
            # Validate input
            if response_type == "regex":
                pattern = meta_config.get("response_regex", "")
                if not re.match(pattern, user_message):
                    return {
                        "result": "error",
                        "message": f"Invalid format for {key}. Please follow the required format.",
                    }
            elif response_type == "list":
                allowed_values = meta_config.get("response_list", [])
                if user_message not in allowed_values:
                    return {
                        "result": "error",
                        "message": f"Invalid input for {key}. Allowed values: {', '.join(allowed_values)}.",
                    }
            elif response_type == "string":
                if not user_message.strip():
                    return {
                        "result": "error",
                        "message": f"Please provide a non-empty value for {key}.",
                    }

            # If passed validation
            doc_state["doc_data"][key] = user_message
            doc_state["last_message_prompt"] = ""
            return {"result": "stored"}

        # If we haven't prompted for this key yet
        if last_prompt != key:
            doc_state["last_message_prompt"] = key
            return {"result": "prompt", "message": meta_config["prompt"]}

        # Fallback
        return {"result": "error", "message": "An unexpected error occurred."}

    def generate_document(self, doc_data: Dict[str, Any]) -> str:
        return (
            "=== GENERATED DOCUMENT ===\n"
            f"Name: {doc_data.get('name', '')}\n"
            f"Favorite Color: {doc_data.get('favorite_color', '')}\n"
            f"Email: {doc_data.get('email', '')}\n"
            f"Hobby: {doc_data.get('hobby', '')}\n"
            f"Country: {doc_data.get('country', '')}\n"
            "=== END OF DOCUMENT ===\n"
        )


# === FLOWS ===
doc_metadata = [
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
doc_creation_flow = DocumentCreationFlow(doc_metadata=doc_metadata)
