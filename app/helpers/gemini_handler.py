"""
File for the Gemini API

Classes:
    model (GenerativeModel): Instance of GenerativeModel.
    GeminiHandler: Handlers for the Gemini API.
"""

import os
import logging
import google.generativeai as genai

logging.basicConfig(level=logging.INFO)


class GeminiHandler:
    """
    Handlers for the Gemini API

    Attributes:
        model (GenerativeModel): Instance of GenerativeModel.

    Methods:
        __init__():
            Initialize the GeminiHandler.
    """

    def __init__(self):
        """
        Initialize the GeminiHandler
        """
        try:
            genai.configure(api_key=os.environ["GOOGLE_GENAI_API_KEY"])
            self.model = genai.GenerativeModel(
                model_name=os.environ["GOOGLE_GENAI_MODEL"]
            )
            logging.info("GeminiHandler initialized")
        except Exception as e:
            logging.error(e)
