import json
import logging
from typing import Any, Dict, List, Optional

from mistralai import AsyncMistral
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from database.SQLModel import Alice
from .schemas import GeneratedCVData
from .latex_renderer import LaTeXRenderer

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an elite ATS CV Strategist and Executive Resume Writer.

Your objective:
Generate structured CV content tailored to a target job description using retrieved candidate experiences and metadata.

Strict Rules:
1. Grounding: Rely strictly on candidate profile and retrieved facts. Do not invent companies, degrees, dates, metrics, or credentials.
2. Tailoring: Prioritize skills, bullets, and technical terms directly referenced in the job offer.
3. Impact: Format bullets using the Action Verb + Context + Result (with metrics if available in context) structure.
4. ATS Formatting: Ensure skill categorizations match standard industry conventions.
5. Response: Return structured JSON matching the provided schema.
"""

class GenerationService:
    def __init__(
        self,
        api_key: str,
        model: str = "mistral-large-latest",
        renderer: Optional[LaTeXRenderer] = None,
    ):
        self.client = AsyncMistral(api_key=api_key)
        self.model = model
        self.renderer = renderer or LaTeXRenderer()

    async def generate_cv(
        self,
        username: str,
        session: AsyncSession,
        offer_extraction: Dict[str, Any],
        best_experiences: Dict[str, Any],
        best_projects: Dict[str, Any],
    ) -> str:
        user_result = await session.execute(select(Alice).where(Alice.name == username))
        user = user_result.scalar_one_or_none()
        if user is None:
            raise ValueError(f"No user found for username: {username}")

        user_profile = {
            "name": user.name,
            "education": user.education,
            "number": user.number,
            "address": user.address,
            "email_address": user.email_address,
        }

        _, latex_source = await self.generate_tailored_cv(
            user_profile=user_profile,
            job_offer=offer_extraction,
            retrieved_experiences=best_experiences.get("experiences", []),
            retrieved_projects=best_projects.get("projects", []),
        )
        return latex_source

    async def generate_tailored_cv(
        self,
        user_profile: Dict[str, Any],
        job_offer: Dict[str, Any],
        retrieved_experiences: List[Dict[str, Any]],
        retrieved_projects: List[Dict[str, Any]],
    ) -> tuple[GeneratedCVData, str]:
        """
        Executes LLM structured synthesis and deterministically renders to LaTeX.
        Returns: (GeneratedCVData, latex_source_string)
        """
        payload = self._assemble_prompt(
            user=user_profile,
            offer=job_offer,
            experiences=retrieved_experiences,
            projects=retrieved_projects,
        )

        try:
            response = await self.client.chat.parse_async(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": payload},
                ],
                response_format=GeneratedCVData,
                temperature=0.2, # Low temperature for factual consistency
            )
            
            structured_data: GeneratedCVData = response.choices[0].message.parsed
            
            # Deterministic, safe rendering
            latex_source = self.renderer.render(structured_data)
            return structured_data, latex_source

        except Exception as err:
            logger.error(f"Failed to generate structured CV: {str(err)}", exc_info=True)
            raise RuntimeError(f"CV Generation Pipeline Error: {err}") from err

    def _assemble_prompt(
        self,
        user: Dict[str, Any],
        offer: Dict[str, Any],
        experiences: List[Dict[str, Any]],
        projects: List[Dict[str, Any]],
    ) -> str:
        return f"""### TARGET JOB DESCRIPTION
{json.dumps(offer, indent=2)}

### CANDIDATE BASE PROFILE
{json.dumps(user, indent=2)}

### RETRIEVED RELEVANT EXPERIENCES (RAG)
{json.dumps(experiences, indent=2)}

### RETRIEVED RELEVANT PROJECTS (RAG)
{json.dumps(projects, indent=2)}

Synthesize this data into the required structured CV output. Prioritize high-relevance matches for the target role."""