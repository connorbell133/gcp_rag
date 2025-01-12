from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


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
