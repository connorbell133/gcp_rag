import logging
from fastapi import FastAPI, Request

from app.helpers.gemini_handler import GeminiHandler
from app.helpers.meta_config import MetaDataConfig
from app.flows.doc_generation import DocumentCreationFlow
from app.orchestrators.doc_generation import (
    DocumentCreationFlow as DocumentCreationOrchestrator,
)
from app.universal_data import convo_state_handler

# --- Logging & App ---
logging.basicConfig(level=logging.INFO)
app = FastAPI()

# --- Flow Registry ---
flows_registry = {
    "document_creation": {"flow": DocumentCreationFlow(), "type": "flow"},
    "document_creation_orchestrator": {
        "flow": DocumentCreationOrchestrator(),
        "type": "orchestrator",
    },
}

# --- Metadata Configuration ---
metadata_config = MetaDataConfig()


@app.post("/response")
async def post_endpoint(request: Request):

    # 0) Parse incoming message
    data = await request.json()
    conversation_id = data["conversation_id"]
    message = data["message"]

    logging.info(
        "Received message '%s' for conversation_id '%s'", message, conversation_id
    )

    # 1) Retrieve or create the conversation state
    metadata_config.get_or_create_conversation_state(conversation_id)
    conversation_state = convo_state_handler[conversation_id]
    logging.info("Current conversation state: %s", conversation_state)

    # 2) If base metadata isn't set, handle that first
    # if not conversation_state["base_metadata_set"]:
    #     result = metadata_config.handle_base_metadata(conversation_state, message)

    #     if isinstance(result, dict):
    #         # Returning a dict with a "message"
    #         return {"message": result["message"], "done": "yes"}
    #     elif isinstance(result, str):
    #         # Returning a string prompt
    #         return {"message": result, "done": "yes"}
    #     else:
    #         # Base metadata is fully collected
    #         conversation_state["base_metadata_set"] = True
    #         conversation_state["current_subtask"] = "None"
    #         conversation_state["subtask_status"] = "none"
    #         valid_flows = "', '".join(flows_registry.keys())

    #         return {
    #             "message": f"Base metadata is set! Which flow would you like to start? Available flows: '{valid_flows}'",
    #             "done": "no",
    #         }
    # logging.info("Base metadata is set")

    logging.info("Current conversation state: %s", conversation_state)
    # 3) Base metadata is set: either pick a flow or continue the current one
    if conversation_state["current_subtask"] == "none":
        logging.info("User hasn't picked a flow yet")
        # User hasn't picked a flow yet
        chosen_flow = message.strip().lower()
        if chosen_flow != "none":
            if chosen_flow in flows_registry:
                conversation_state["current_subtask"] = chosen_flow
                conversation_state["subtask_status"] = "in_progress"
                return {
                    "message": f"Great, starting subtask: {chosen_flow}!",
                    "done": "no",
                }
            else:
                valid_flows = ", ".join(flows_registry.keys())
                return {
                    "message": f"Invalid flow choice. Please choose from: {valid_flows}",
                    "done": "no",
                }
    else:
        # User has a flow in progress
        current_flow_key = conversation_state["current_subtask"]

        # Check if the flow is in the registry
        if current_flow_key in flows_registry:
            flow = flows_registry[current_flow_key]
            logging.info("Handling flow: %s", current_flow_key)
            # Check if the flow is complete
            if not flow["flow"].is_complete(conversation_id):
                logging.info("Flow is not complete")
                # Handle orchestrator flows differently
                if flow["type"] == "orchestrator":
                    logging.info("Handling orchestrator flow")
                    flow_result = flow["flow"].orchestrate(message, conversation_id)
                else:
                    logging.info("Handling regular flow for message: %s", message)
                    flow_result = flow["flow"].handle_step(message, conversation_id)
                if flow_result:
                    logging.info("Flow result: %s", flow_result)
                    return {
                        "message": flow_result["message"],
                        "done": flow_result["done"],
                    }
            else:
                # Flow is complete, reset for next flow
                conversation_state["current_subtask"] = "None"
                conversation_state["subtask_status"] = "none"
                return {
                    "message": f"The {current_flow_key} flow is complete. Anything else? If not, say 'none'.",
                    "done": "yes",
                }
        else:
            valid_flows = ", ".join(flows_registry.keys())
            return {
                "message": f"Unknown flow '{current_flow_key}'. Available flows: {valid_flows}",
                "done": "no",
            }

    # 4) Fallback: pass the message to GeminiHandler
    response_text = (
        GeminiHandler().model.generate_content({"text": message}, stream=False).text
    )
    return {"message": response_text, "done": "yes"}
