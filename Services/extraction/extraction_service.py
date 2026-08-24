import ast
from .models import ExtractionSchema
from mistralai.client import Mistral
from .prompts.prompts import PARSE_QUESTION_SYSTEM_PROMPT, PARSE_QUESTION_USER_TEMPLATE


class ExtractionService:
    def __init__(self, api_key: str):
        self.model:str = "mistral-large-latest"
        self.MISTRAL_API_KEY:str = api_key


    def extract(self, text: str, system_prompt: str = PARSE_QUESTION_SYSTEM_PROMPT,user_template: str = PARSE_QUESTION_USER_TEMPLATE): 
        user_msg = user_template.format(question=text)
        Client = Mistral(api_key=self.MISTRAL_API_KEY)
        extracted = Client.chat.parse(
                model=self.model,
                messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
                ],
                response_format=ExtractionSchema, # Pydantic model
                )
        extracted_dict = self.extract_dict_from_string(extracted.choices[0].message.content)

        return extracted_dict


    def extract_dict_from_string(self, extraction_string: str):
        """
        Extracts a Python dictionary from a string representation.
        Safely evaluates the string using ast.literal_eval.
        """
        try:
            trys = extraction_string.strip()
            result = ast.literal_eval(trys)

            if not isinstance(result, dict):
                raise ValueError("The string does not represent a dictionary.")
            return result

        except (SyntaxError, ValueError) as e:
            print(f"Error: {e}")
            return None
        
