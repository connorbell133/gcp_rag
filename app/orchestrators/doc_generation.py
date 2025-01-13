from typing import List, Dict, Any
from app.orchestrators.BaseOrchestrator import BaseOrchestrator
from app.flows.BaseFlow import BaseFlow
from app.universal_data import (
    validate_and_store_doc_data,
    get_subtask_state,
)


# === SUBFLOWS (unchanged) ===
class IntroductionFlow(BaseFlow):
    def __init__(
        self,
        doc_metadata: List[Dict[str, Any]],
        index: str,
    ):
        self.doc_metadata = doc_metadata
        self.index = index

    def handle_step(self, user_message: str, conversation_id: str):
        questions = self.doc_metadata[:3]
        for meta_config in questions:
            key = meta_config["key"]
            doc_state = get_subtask_state(conversation_id, "document_creation_orch")
            if key not in doc_state["doc_data"]:
                result = validate_and_store_doc_data(
                    doc_state,
                    user_message,
                    meta_config,
                    index=self.index,
                )
                if result["result"] == "stored":
                    continue
                elif result["result"] in ("prompt", "error"):
                    return {"message": result["message"], "done": "no"}

        if self.is_complete(conversation_id):
            return {"message": "Introduction done!", "done": "yes"}
        else:
            return {"message": "Still missing data for IntroductionFlow.", "done": "no"}

    def is_complete(self, conversation_id: str) -> bool:
        doc_state = get_subtask_state(conversation_id, "document_creation_orch")
        return len(doc_state["doc_data"]) >= 3


class MiddleFlow(BaseFlow):
    def __init__(
        self,
        doc_metadata: List[Dict[str, Any]],
        index: str,
    ):
        self.doc_metadata = doc_metadata
        self.index = index

    def handle_step(self, user_message: str, conversation_id: str):
        questions = self.doc_metadata[3:4]  # Only one question in this flow
        for meta_config in questions:
            key = meta_config["key"]
            doc_state = get_subtask_state(conversation_id, "document_creation_orch")
            if key not in doc_state["doc_data"]:
                result = validate_and_store_doc_data(
                    doc_state, user_message, meta_config, index=self.index
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
        doc_state = get_subtask_state(conversation_id, "document_creation_orch")
        return len(doc_state["doc_data"]) >= 4


class EndFlow(BaseFlow):
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
            doc_state = get_subtask_state(conversation_id, "document_creation_orch")
            if key not in doc_state["doc_data"]:
                result = validate_and_store_doc_data(
                    doc_state, user_message, meta_config, index=self.index
                )
                if result["result"] == "stored":
                    continue
                elif result["result"] in ("prompt", "error"):
                    return {"message": result["message"], "done": "no"}

        if self.is_complete(conversation_id):
            return {"message": "Middle done!", "done": "yes"}
        else:
            return {"message": "Still missing data for EndFlow.", "done": "no"}

    def is_complete(self, conversation_id: str) -> bool:
        doc_state = get_subtask_state(conversation_id, "document_creation_orch")
        return len(doc_state["doc_data"]) >= 5


class GenerateDocument(BaseFlow):
    def __init__(
        self,
        doc_metadata: List[Dict[str, Any]],
        index: str,
    ):
        self.doc_metadata = doc_metadata
        self.index = index

    def handle_step(self, user_message: str, conversation_id: str):
        doc_state = get_subtask_state(conversation_id, "document_creation_orch")
        doc_state["doc_data_completed"] = True

        if self.is_complete(conversation_id):
            return self.generate_document(doc_state["doc_data"])
        else:
            return {"message": "Still missing data for EndFlow.", "done": "no"}

    def is_complete(self, conversation_id: str) -> bool:
        doc_state = get_subtask_state(conversation_id, "document_creation_orch")
        return doc_state["doc_data_completed"]

    def generate_document(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
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


# === MAIN FLOW (Orchestrator) ===
class DocumentCreationFlow(BaseOrchestrator):
    """
    Guides the user through creating a document by letting them pick subflows
    or leave the flow at any time.

    Subflows:
      - 'introduction'
      - 'middle'
      - 'end'
      - 'generate'
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
            "introduction": IntroductionFlow(
                self.doc_metadata,
                "doc_creation_orch",
            ),
            "middle": MiddleFlow(
                self.doc_metadata,
                "doc_creation_orch",
            ),
            "end": EndFlow(
                self.doc_metadata,
                "doc_creation_orch",
            ),
            "generate": GenerateDocument(
                self.doc_metadata,
                "doc_creation_orch",
            ),
        }

    def orchestrate(self, user_message: str, conversation_id: str) -> Dict[str, Any]:
        """
        Allows the user to pick any subflow from 'introduction', 'middle', 'end', 'generate'
        or to 'leave' the flow at any time. If a subflow is currently in progress,
        we send user_message to it. Once that subflow's handle_step returns done="yes",
        we reset the subflow so the user can choose another one.
        """
        # Standardize user_message
        user_message = user_message.strip().lower()

        doc_state = get_subtask_state(conversation_id, "document_creation_orch")
        current_subflow = doc_state.get(
            "current_subflow"
        )  # None or e.g. "introduction"

        # 1) If user wants to leave
        if user_message == "leave":
            doc_state["doc_data_completed"] = True
            doc_state["current_subflow"] = None
            return {
                "message": "You have left the document creation flow.",
                "done": "yes",
            }

        # 2) If there's no active subflow, see if user wants to pick one
        if not current_subflow:
            # If user typed the name of a subflow, start that subflow
            if user_message in self.subflows:
                doc_state["current_subflow"] = user_message
                return {
                    "message": f"Starting subflow '{user_message}'. Please proceed.",
                    "done": "no",
                }
            else:
                # Prompt user to pick from available subflows
                subflow_list = ", ".join(self.subflows.keys())
                return {
                    "message": f"Which subflow would you like to use? "
                    f"Available: {subflow_list}. Or say 'leave' to exit.",
                    "done": "no",
                }

        # 3) We have a current subflow: pass the message to it
        flow = self.subflows[current_subflow]
        flow_result = flow.handle_step(user_message, conversation_id)

        # If the subflow is done, reset subflow so user can choose next
        if flow_result["done"] == "yes":
            doc_state["current_subflow"] = None

            # If the entire doc data is completed, we can also set doc_data_completed
            # or just let the user pick subflows again. For example:
            if self.is_complete(conversation_id):
                return {
                    "message": (
                        f"'{current_subflow}' is complete, and it looks like all data is collected!\n"
                        "You can say 'generate' to produce the document, or 'leave' to exit."
                    ),
                    "done": "no",
                }

            return {
                "message": (
                    f"Subflow '{current_subflow}' is complete. "
                    f"Pick another subflow or say 'leave' to exit."
                ),
                "done": "no",
            }

        return flow_result

    def is_complete(self, conversation_id: str) -> bool:
        """
        Returns True if the doc data is fully completed (and/or the user has
        indicated it's done). This might mean the user has run 'generate'
        or otherwise signaled it's done.
        """
        doc_state = get_subtask_state(conversation_id, "document_creation_orch")
        return bool(doc_state.get("doc_data_completed", False))
