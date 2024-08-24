"""
Class: PromptMaster
Description: This class is responsible for loading and returning prompts from the prompt library.
Methods:
    1. __init__: Initializes the PromptMaster class with the filename of the prompt library.
    2. load_prompts: Loads the prompts from the specified file.
    3. get_prompt: Returns the prompt based on the prompt name and keyword arguments.
"""

import yaml
import logging


class PromptMaster:
    def __init__(self, filename: str) -> None:
        """
        Initializes the PromptMaster class with the filename of the prompt library.
        """
        self.prompts = self.load_prompts(filename=filename)
        logging.info("PromptMaster initialized with prompts: %s", self.prompts)

    def load_prompts(self, filename: str) -> dict:
        """
        Loads the prompts from the specified file.
        """
        with open(f"app/prompt_library/{filename}.yml", "r", encoding="utf-8") as file:
            prompts = yaml.safe_load(file)

        return prompts

    def get_prompt(self, prompt_name: str, **kwargs) -> str:
        """
        Returns the prompt based on the prompt name and keyword arguments.
        """
        try:
            prompt = self.prompts[prompt_name]["prompt"]
            # for each key in kwargs, replace the corresponding value in the prompt

            if isinstance(prompt, str):
                try:
                    # turn all kwarg vakues into strings
                    for key, value in kwargs.items():
                        kwargs[key] = str(value)

                    return prompt.format(**kwargs)
                except KeyError as e:
                    return f"Key {e} not found in kwargs"
            else:
                return f"Prompt {prompt_name} is not a string"
        except KeyError:
            return f"Prompt {prompt_name} not found"
        except Exception as e:
            return f"An error occurred: {e}"
