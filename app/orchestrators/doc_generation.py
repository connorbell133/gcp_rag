from typing import List, Dict, Any
from app.orchestrators.BaseOrchestrator import BaseOrchestrator
from app.flows.BaseFlow import BaseFlow
from app.universal_data import (
    validate_and_store_doc_data,
    get_doc_state,
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
            doc_state = get_doc_state(conversation_id)
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
        doc_state = get_doc_state(conversation_id)
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
            doc_state = get_doc_state(conversation_id)
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
        doc_state = get_doc_state(conversation_id)
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
            doc_state = get_doc_state(conversation_id)
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
        doc_state = get_doc_state(conversation_id)
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
        doc_state = get_doc_state(conversation_id)
        doc_state["doc_data_completed"] = True

        if self.is_complete(conversation_id):
            return self.generate_document(doc_state["doc_data"])
        else:
            return {"message": "Still missing data for EndFlow.", "done": "no"}

    def is_complete(self, conversation_id: str) -> bool:
        doc_state = get_doc_state(conversation_id)
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

        doc_state = get_doc_state(conversation_id)
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
        doc_state = get_doc_state(conversation_id)
        return bool(doc_state.get("doc_data_completed", False))

    # def get_doc_state(self, conversation_id) -> Dict[str, Any]:
    #     """
    #     Retrieve or create the doc_state from conversation_state.
    #     """
    #     subtask_data = convo_state_handler[conversation_id]["subtask_data"].get(
    #         "document_creation"
    #     )
    #     if not subtask_data:
    #         convo_state_handler[conversation_id]["subtask_data"][
    #             "document_creation"
    #         ] = {
    #             "status": "in_progress",
    #             "data": {
    #                 "doc_data": {},
    #                 "doc_data_completed": False,
    #                 "last_message_prompt": "",
    #                 # We'll store the active subflow key here, if any
    #                 "current_subflow": None,
    #             },
    #         }
    #         subtask_data = convo_state_handler[conversation_id]["subtask_data"][
    #             "document_creation"
    #         ]
    #     return subtask_data["data"]

    # def validate_and_store_doc_data(
    #     self,
    #     doc_state: Dict[str, Any],
    #     user_message: str,
    #     meta_config: Dict[str, Any],
    #     index: str,
    # ) -> Dict[str, Any]:
    #     """
    #     Attempts to validate and store user_message into doc_state["doc_data"][<key>]
    #     according to meta_config (prompt, response_type, etc.).
    #     """
    #     key = meta_config["key"]
    #     last_prompt = doc_state["last_message_prompt"]
    #     response_type = meta_config.get("response_type", "string")

    #     # Only validate if the user is actually responding to the last prompt
    #     if last_prompt == key:
    #         if response_type == "regex":
    #             pattern = meta_config.get("response_regex", "")
    #             if not re.match(pattern, user_message):
    #                 return {
    #                     "result": "error",
    #                     "message": f"Invalid format for {key}. Please try again.",
    #                 }
    #         elif response_type == "list":
    #             allowed_values = meta_config.get("response_list", [])
    #             if user_message not in allowed_values:
    #                 allowed_str = ", ".join(allowed_values)
    #                 return {
    #                     "result": "error",
    #                     "message": f"Invalid input for {key}. Allowed values: {allowed_str}.",
    #                 }
    #         elif response_type == "string":
    #             if not user_message.strip():
    #                 return {
    #                     "result": "error",
    #                     "message": f"Please provide a non-empty value for {key}.",
    #                 }
    #         # If passed validation:
    #         doc_state[index]["doc_data"][key] = user_message
    #         doc_state["last_message_prompt"] = ""
    #         return {"result": "stored"}

    #     # If we haven't prompted for this key yet, prompt now
    #     if last_prompt != key:
    #         doc_state["last_message_prompt"] = key
    #         return {"result": "prompt", "message": meta_config["prompt"]}

    #     # Fallback
    #     return {"result": "error", "message": "An unexpected error occurred."}
