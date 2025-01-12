import logging
from typing import TypedDict, Dict, Any

from fastapi import FastAPI, Request

from app.helpers.gemini_handler import GeminiHandler
from app.helpers.meta_config import MetaDataConfig
from app.flows.doc_generation import (
    doc_creation_flow,
)
from app.universal_data import convo_state_handler

# === FLOW REGISTRY ===
flows_registry = {
    # "base_metadata": base_metadata_flow,
    "document_creation": doc_creation_flow,
}

# === LOGGING & FASTAPI APP ===
logging.basicConfig(level=logging.INFO)
app = FastAPI()

# === METADATA CONFIGURATION ===
metadata_config = MetaDataConfig()


# === ENDPOINTS ===
@app.post("/response")
async def post_endpoint(request: Request):
    data = await request.json()
    conversation_id = data["conversation_id"]
    message = data["message"]

    logging.info(
        "Received message: %s for conver    sation_id: %s", message, conversation_id
    )

    # 1) Get or create conversation state
    metadata_config.get_or_create_conversation_state(conversation_id)
    logging.info("Current conversation state: %s", convo_state_handler[conversation_id])

    # 2) If base metadata not yet set, handle that first
    if not convo_state_handler[conversation_id]["base_metadata_set"]:
        result = metadata_config.handle_base_metadata(
            convo_state_handler[conversation_id], message
        )
        if isinstance(result, dict):
            # result has a "message" we want to return
            return {"message": result["message"], "done": "yes"}
        elif isinstance(result, str):
            # If it's a string, treat it as a prompt
            return {"message": result, "done": "yes"}
        else:
            # Base metadata collection completed
            convo_state_handler[conversation_id]["base_metadata_set"] = True
            convo_state_handler[conversation_id]["current_subtask"] = "None"
            convo_state_handler[conversation_id]["subtask_status"] = "none"

            # Prompt the user to pick a flow from flows_registry
            valid_flows = "', '".join(flows_registry.keys())
            return {
                "message": f"Base metadata is set! Which flow would you like to start next? Available flows: {valid_flows}",
                "done": "no",
            }
    else:
        # 2.5) Base metadata is set, so check if we need to pick a subtask
        if convo_state_handler[conversation_id]["current_subtask"] == "None":
            # The user hasn't picked a flow yet, so interpret this message as the flow choice
            chosen_flow = message.strip().lower()  # user typed e.g. 'document_creation'
            if chosen_flow != "none":
                if chosen_flow in flows_registry:
                    convo_state_handler[conversation_id][
                        "current_subtask"
                    ] = chosen_flow
                    convo_state_handler[conversation_id][
                        "subtask_status"
                    ] = "in_progress"
                    return {
                        "message": f"Great, starting subtask: {chosen_flow}!",
                        "done": "no",
                    }
                else:
                    # Invalid flow choice
                    valid_flows = ", ".join(flows_registry.keys())
                    return {
                        "message": f"Invalid flow choice. Please choose one of: {valid_flows}",
                        "done": "no",
                    }
        else:
            # 3) If we have a "current_subtask" set, run it
            current_flow_key = convo_state_handler[conversation_id]["current_subtask"]
            if current_flow_key in flows_registry:
                flow = flows_registry[current_flow_key]
                # e.g. doc_creation_flow or some_other_flow

                if not flow.is_complete(conversation_id):
                    flow_result = flow.handle_step(message, conversation_id)
                    if flow_result:
                        return {
                            "message": flow_result["message"],
                            "done": flow_result["done"],
                        }
                else:
                    # If flow is already complete, maybe ask the user if they want another flow
                    # or just say "Flow is complete"
                    # set current_subtask to "None" to allow user to pick another flow
                    convo_state_handler[conversation_id]["current_subtask"] = "None"
                    convo_state_handler[conversation_id]["subtask_status"] = "none"

                    return {
                        "message": f"The {current_flow_key} flow is complete. Anything else? if not, say 'none'",
                        "done": "yes",
                    }
            else:
                # If for some reason the subtask is invalid
                valid_flows = ", ".join(flows_registry.keys())
                return {
                    "message": f"Unknown subtask: {current_flow_key}. Available: {valid_flows}",
                    "done": "no",
                }

    # 4) Otherwise, normal conversation logic
    response_text = (
        GeminiHandler().model.generate_content({"text": message}, stream=False).text
    )
    return {"message": response_text, "done": "yes"}
