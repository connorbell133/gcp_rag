import asyncio
import websockets

import json
import requests
import random


async def chat_with_rag():
    uri = "ws://localhost:8080/response"
    async with websockets.connect(uri) as websocket:
        print("Connected to the WebSocket server")

        while True:
            message = input("Enter your message: ")
            if message.lower() == "exit":
                print("Exiting chat.")
                break

            await websocket.send(json.dumps({"message": message}))
            print("Message sent to the server")
            full_response = ""
            while True:
                # resposne is a json object
                response = await websocket.recv()
                response = json.loads(response)
                print(response["message"])
                # Check if the response is the last message
                if response["done"] == "yes":
                    break
                full_response += response["message"]
            print(f"Message received from the server: {full_response}")


def create_message(message, conversation_id, sender="user"):
    """
    Create a message object

    Args:
        message (str): The message content
        conversation_id (str): The conversation ID
        sender (str): The sender of the message

    Returns:
        dict: The message object
    """
    return {
        "message": message,
        "sender": sender,
        "conversation_id": conversation_id,
        "message_id": str(random.randint(1000000, 9999999)),
    }


def chat_with_rag_post():
    """
    Chat with the RAG model using POST requests
    """
    uri = "http://localhost:8080/response"
    print("Connected to the server")
    conversation_id = str(random.randint(1000000, 9999999))
    conversation = []
    while True:
        message = input("-------------------- User Message --------------------\n")
        if message.lower() == "exit":
            break

        # Create a message object
        message_obj = create_message(message, conversation_id)
        conversation.append(message_obj)

        # Send the message to the server
        body = json.dumps({"message": message, "conversation_id": conversation_id})
        response = requests.post(uri, data=body).json()

        # Get the response from the server
        response_message = create_message(
            response["message"], conversation_id, "assistant"
        )
        conversation.append(response_message)
        print("-------------------- AI Message --------------------")
        print(response["message"])


chat_with_rag_post()
