"""
Class: FastAPI
Description: This is the main file that contains the FastAPI instance and the WebSocket endpoint.
Endpoints:
    1. /ws/response: This is the WebSocket endpoint that receives the incoming message, 
    gets the response from the responseHandler, and sends the response back through the WebSocket.
    
"""

import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.helpers.gemini_handler import GeminiHandler
from app.response_master import responseHandler

logging.basicConfig(level=logging.INFO)
app = FastAPI()
origins = [
    "http://localhost:3000",  # adjust to match the domain of your client app
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/ws/response")
async def websocket_endpoint(websocket: WebSocket):
    """
    1. Accept the WebSocket connection
    2. Receive the incoming message from the WebSocket
    3. Get the response from the responseHandler
    4. Send the response back through the WebSocket
    """

    await websocket.accept()
    try:
        while True:
            # Receive incoming message
            data = await websocket.receive_json()
            incoming_msg = data["message"]

            # Generate Prompt from incoming message
            prompt = responseHandler().get_response(incoming_msg)

            if prompt["result"]:
                if prompt["type"] == "response":
                    await websocket.send_text(prompt["response"])
                    continue
                elif prompt["type"] == "prompt":
                    logging.info("Response found in cache")
                    # Generate response
                    response = GeminiHandler().model.generate_content(
                        {"text": prompt["response"]}, stream=True
                    )

                    # Stream response back to client
                    for chunk in response:
                        await websocket.send_text(chunk.text)
                else:
                    logging.info("Error in response type")
                    await websocket.send_text("error")
            else:
                logging.info("No response found in cache")
                await websocket.send_text("No response found")
    except WebSocketDisconnect:
        logging.info("Client disconnected")
