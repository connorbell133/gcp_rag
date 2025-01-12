import logging
from typing import TypedDict, Dict, Any


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
