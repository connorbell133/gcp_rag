from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Callable


class BaseFlow(ABC):
    """
    Abstract base class for flows, requiring handle_step and is_complete
    methods. Each flow manages its own state and uses config-driven logic.
    """

    @abstractmethod
    def handle_step(
        self, user_message: str, conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Process the user_message within the context of the flow.

        Returns an optional dict with:
         - "message": The response to be displayed
         - "done": "yes"/"no" to indicate if flow is complete
        """

    @abstractmethod
    def is_complete(self, conversation_id: str) -> bool:
        """
        Check if this flow is complete based on the conversation_state.
        """


def gather_store_vars(
    questions: list,
    conversation_id: str,
    user_message: str,
    index: str,
    is_complete: Callable,
    get_subtask_state: Callable,
    validate_and_store_doc_data: Callable,
):
    """
    Gather and store variables for a subtask based on a list of questions.

    This function is used by the DocumentCreationFlow to gather and store

    """
    for meta_config in questions:
        key = meta_config["key"]
        doc_state = get_subtask_state(conversation_id, "document_creation_orchestrator")
        if key not in doc_state["data"]["subtask_data"]:
            result = validate_and_store_doc_data(
                doc_state["data"],
                user_message,
                meta_config,
                index,
            )
            if result["result"] == "stored":
                continue
            elif result["result"] in ("prompt", "error"):
                return {"message": result["message"], "done": "no"}

        if is_complete(conversation_id):
            return {"message": "Subflow done!", "done": "yes"}
        else:
            return {"message": "Still missing data for Subflow.", "done": "no"}
