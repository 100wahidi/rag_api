import ast
from modules.extraction.models import ExractionItem
from modules.core.prompts import PARSE_QUESTION_SYSTEM_PROMPT, PARSE_QUESTION_USER_TEMPLATE
from modules.core.logs import setup_logger
from modules.core.llm import AsyncGroqProvider 

logger = setup_logger(__name__)

class ExtractionService:

    def __init__(self, client: AsyncGroqProvider = None):
        self.client = client 
    
    async def extract(
                    self, text: str,
                    system_prompt: str = PARSE_QUESTION_SYSTEM_PROMPT,
                    user_template: str = PARSE_QUESTION_USER_TEMPLATE,
                    response_model= ExractionItem,
                    ): 
        
            user_msg = user_template.format(question=text)

            Client = self.client 

            if not Client:
                raise ValueError("Client is not served. Please provide a valid API key.")
            else:
                logger.info("Client is served. Proceeding with extraction.")
                try:
                    extracted = await Client.generate_structured(
                        system_prompt=system_prompt,
                        user_prompt=user_msg,
                        response_format=response_model
                    )
                    
                except Exception as e:
                    logger.error("Error during extraction: %s", e)
                    raise ValueError(f"Extraction failed: {e}")
                
                logger.info("Extraction results: %s", extracted)

                return extracted


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
            return None
        
