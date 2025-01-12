import logging
from typing import TypedDict, Dict, Any
import re

# === LOGGING & FASTAPI APP ===
logging.basicConfig(level=logging.INFO)


# === DATA STRUCTURES / TYPE DEFINITIONS ===
class Subtask(TypedDict):
    """Subtask data structure"""

    status: str
    data: Dict[str, Any]


class ConversationState(TypedDict):
    """Conversation state data structure"""

    conversation_id: str
    base_metadata: Dict[str, Any]
    base_metadata_set: bool
    nested_position: str
    current_subtask: str
    subtask_status: str
    subtask_data: Dict[str, Subtask]
    last_message_prompt: str
    last_updated: str


# === IN-MEMORY STORE ===
convo_state_handler: Dict[str, ConversationState] = {}

# === METADATA CONFIGURATION ===
provider_metadata = [
    {
        "key": "email",
        "prompt": "Please provide your email address.",
        "response_regex": r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
        "response_type": "regex",
        "response_list": [],
    },
    {
        "key": "username",
        "prompt": "Please provide your username.",
        "response_regex": "",
        "response_type": "list",
        "response_list": ["connorbell", "connor"],
    },
]


# === MAIN ===


def get_doc_state(conversation_id) -> Dict[str, Any]:
    """
    Retrieve or create the doc_state from conversation_state.
    """
    subtask_data = convo_state_handler[conversation_id]["subtask_data"].get(
        "document_creation"
    )
    if not subtask_data:
        convo_state_handler[conversation_id]["subtask_data"]["document_creation"] = {
            "status": "in_progress",
            "data": {
                "doc_data": {},
                "doc_data_completed": False,
                "last_message_prompt": "",
                # We'll store the active subflow key here, if any
                "current_subflow": None,
            },
        }
        subtask_data = convo_state_handler[conversation_id]["subtask_data"][
            "document_creation"
        ]
    return subtask_data["data"]


def validate_and_store_doc_data(
    doc_state: Dict[str, Any],
    user_message: str,
    meta_config: Dict[str, Any],
    index: str,
) -> Dict[str, Any]:
    """
    Attempts to validate and store user_message into doc_state["doc_data"][<key>]
    according to meta_config (prompt, response_type, etc.).
    """
    key = meta_config["key"]
    last_prompt = doc_state["last_message_prompt"]
    response_type = meta_config.get("response_type", "string")

    # Only validate if the user is actually responding to the last prompt
    if last_prompt == key:
        if response_type == "regex":
            pattern = meta_config.get("response_regex", "")
            if not re.match(pattern, user_message):
                return {
                    "result": "error",
                    "message": f"Invalid format for {key}. Please try again.",
                }
        elif response_type == "list":
            allowed_values = meta_config.get("response_list", [])
            if user_message not in allowed_values:
                allowed_str = ", ".join(allowed_values)
                return {
                    "result": "error",
                    "message": f"Invalid input for {key}. Allowed values: {allowed_str}.",
                }
        elif response_type == "string":
            if not user_message.strip():
                return {
                    "result": "error",
                    "message": f"Please provide a non-empty value for {key}.",
                }
        # If passed validation:
        doc_state[index]["doc_data"][key] = user_message
        doc_state["last_message_prompt"] = ""
        return {"result": "stored"}

    # If we haven't prompted for this key yet, prompt now
    if last_prompt != key:
        doc_state["last_message_prompt"] = key
        return {"result": "prompt", "message": meta_config["prompt"]}

    # Fallback
    return {"result": "error", "message": "An unexpected error occurred."}
