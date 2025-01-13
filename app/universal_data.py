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


def get_subtask_state(conversation_id, subtask: str) -> Subtask:
    """
    Retrieve or create the doc_state from conversation_state.
    """
    logging.info(
        "Retrieving subtask state for conversation_id '%s' and subtask '%s'",
        conversation_id,
        subtask,
    )

    subtask_data = convo_state_handler[conversation_id]["subtask_data"].get(
        subtask, None
    )

    logging.info("Subtask data: %s", subtask_data)
    if not subtask_data:
        logging.info("Creating new subtask data for subtask '%s'", subtask)

        convo_state_handler[conversation_id]["subtask_data"][subtask] = {
            "status": "in_progress",
            "data": {
                "subtask_data": {},
                "subtask_completed": False,
                "last_message_prompt": "",
                # We'll store the active subflow key here, if any
                "current_subflow": None,
            },
        }
        subtask_data = convo_state_handler[conversation_id]["subtask_data"][subtask]
        logging.info(
            "Updated Conversation State: %s", convo_state_handler[conversation_id]
        )
        return subtask_data

    return subtask_data


def validate_and_store_doc_data(
    subtask_state: Dict[str, Any],
    user_message: str,
    meta_config: Dict[str, Any],
    index: str,
) -> Dict[str, Any]:
    """
    Attempts to validate and store user_message into doc_state["doc_data"][<key>]
    according to meta_config (prompt, response_type, etc.).
    """
    key = meta_config["key"]
    logging.info(
        "Validating and storing user message '%s' for key '%s'", user_message, key
    )
    logging.info("Subtask state: %s", subtask_state)
    logging.info("index config: %s", index)

    last_prompt = subtask_state["last_message_prompt"]
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
        logging.info("Storing user message '%s' for key '%s'", user_message, key)
        logging.info("subtask_state: %s", subtask_state)
        subtask_state["subtask_data"][key] = user_message
        subtask_state["last_message_prompt"] = ""
        return {"result": "stored"}

    # If we haven't prompted for this key yet, prompt now
    if last_prompt != key:
        subtask_state["last_message_prompt"] = key
        return {"result": "prompt", "message": meta_config["prompt"]}

    # Fallback
    return {"result": "error", "message": "An unexpected error occurred."}
