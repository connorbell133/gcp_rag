"""
This module contains the MetaDataConfig class, which is responsible for handling
metadata configuration and validation logic. It is used in the main.py file to
collect and validate metadata from incoming messages.
"""

import logging
import re
from datetime import datetime
from typing import Dict, Any
from app.universal_data import ConversationState, convo_state_handler, provider_metadata

# === LOGGING ===
logging.basicConfig(level=logging.INFO)


class MetaDataConfig:
    """
    Class to handle metadata configuration and validation.

    Attributes:
        - provider_metadata: List of metadata configurations
        - convo_state_handler: In-memory store for conversation states

    Methods:
        - get_or_create_conversation_state(conversation_id: str) -> ConversationState:
            Retrieve an existing conversation state from the in-memory store,
            or create a new one if none exists.
        - handle_base_metadata(conversation_state: ConversationState, message: str):
            Orchestrate the logic for collecting and validating base metadata from
            provider_metadata. Returns either None (if completed), a dict with an
            error/prompt message, or a string with a prompt message (for backward compatibility).
        - validate_and_store_metadata(
            conversation_state: ConversationState,
            message: str,
            meta_config: Dict[str, Any],
        ) -> Dict[str, Any]:
            Checks whether metadata is already prompted for (last_message_prompt).
            If yes, validate user input, store if valid, or return an error if invalid.
            If no prompt yet, returns a prompt request.

    """

    def __init__(
        self,
    ) -> None:
        pass

    # === HELPER METHODS ===
    def get_or_create_conversation_state(
        self, conversation_id: str
    ) -> ConversationState:
        """
        Retrieve an existing conversation state from the in-memory store,
        or create a new one if none exists.
        """
        if conversation_id not in convo_state_handler:
            logging.info(
                "Creating new conversation state for conversation_id: %s",
                conversation_id,
            )
            convo_state_handler[conversation_id] = ConversationState(
                conversation_id=conversation_id,
                base_metadata={},
                base_metadata_set=False,
                nested_position="main",
                current_subtask="none",
                subtask_status="none",
                subtask_data={},
                last_message_prompt="",
                last_updated=str(datetime.now()),
            )
        else:
            logging.info(
                "Retrieved existing conversation state for conversation_id: %s",
                conversation_id,
            )
        return convo_state_handler[conversation_id]

    def handle_base_metadata(self, conversation_state: ConversationState, message: str):
        """
        Orchestrate the logic for collecting and validating base metadata from
        provider_metadata. Returns either None (if completed), a dict with an
        error/prompt message, or a string with a prompt message (for backward compatibility).
        """
        logging.info(
            "Handling base metadata for conversation_state: %s with message: %s",
            conversation_state,
            message,
        )
        # Go through each metadata config in order
        for meta_config in provider_metadata:
            if meta_config["key"] in conversation_state["base_metadata"]:
                # Skip if metadata is already collected
                continue
            result = self.validate_and_store_metadata(
                conversation_state, message, meta_config
            )
            logging.info(
                "Metadata validation result for %s: %s", meta_config["key"], result
            )
            # Result is a dict with "result" among: "stored", "prompt", "error"
            # or "unexpected"
            if result["result"] == "stored":
                # We found and stored the correct metadata. Move on to the next config.
                continue
            elif result["result"] == "prompt":
                # We need to prompt user to provide a valid answer for this metadata
                return {"message": result["message"]}
            elif result["result"] == "error":
                # We have an error (validation fail or unsupported type)
                return {"message": result["message"]}
            elif result["result"] == "unexpected":
                # Should rarely happen if logic is correct
                return {"message": result["message"]}

        # If we finish the loop without returning, all metadata was collected
        return None

    @staticmethod
    def validate_and_store_metadata(
        conversation_state: ConversationState,
        message: str,
        meta_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Checks whether metadata is already prompted for (last_message_prompt).
        If yes, validate user input, store if valid, or return an error if invalid.
        If no prompt yet, returns a prompt request.
        """
        last_prompt = conversation_state["last_message_prompt"]
        conversation_state["current_subtask"] = "base_metadata"
        logging.info(
            "Validating metadata for key: %s with message: %s",
            meta_config["key"],
            message,
        )

        # 1) If user is responding to a direct prompt for this metadata key
        if last_prompt == meta_config["key"]:
            response_type = meta_config["response_type"]
            # Validate user input
            if response_type == "regex":
                # Check against the specified regex
                if not re.match(meta_config["response_regex"], message):
                    logging.info("Invalid format for %s", meta_config["key"])
                    return {
                        "result": "error",
                        "message": (
                            f"Invalid format for {meta_config['key']}. "
                            "Please follow the required format."
                        ),
                    }
            elif response_type == "list":
                # Check if message is in the allowed list
                if message not in meta_config["response_list"]:
                    allowed_values = ", ".join(meta_config["response_list"])
                    logging.info(
                        "Invalid input for %s. Allowed values are: %s",
                        meta_config["key"],
                        allowed_values,
                    )
                    return {
                        "result": "error",
                        "message": (
                            f"Invalid input for {meta_config['key']}. "
                            f"Allowed values are: {allowed_values}."
                        ),
                    }
            else:
                logging.info("Unsupported validation type for %s", meta_config["key"])
                return {
                    "result": "error",
                    "message": (
                        f"Unsupported validation type for {meta_config['key']}."
                    ),
                }

            # Store valid metadata
            conversation_state["base_metadata"][meta_config["key"]] = message
            conversation_state["last_message_prompt"] = ""
            conversation_state["last_updated"] = str(datetime.now())
            logging.info("Stored metadata for key: %s", meta_config["key"])
            return {"result": "stored"}

        # 2) If we haven't prompted the user for this piece of metadata yet
        if last_prompt != meta_config["key"]:
            conversation_state["last_message_prompt"] = meta_config["key"]
            logging.info("Prompting user for metadata key: %s", meta_config["key"])
            return {
                "result": "prompt",
                "message": meta_config["prompt"],
            }

        # 3) Should rarely occur
        logging.info("Unexpected error occurred in metadata validation.")
        return {
            "result": "unexpected",
            "message": "Unexpected error occurred in metadata validation.",
        }
