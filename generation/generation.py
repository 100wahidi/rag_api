import json
import logging
from typing import Optional
from xml.parsers.expat import model
from mistralai.client import Mistral
from sqlalchemy.ext.asyncio import AsyncSession
from .schema import GeneratedCV, RetrievedExperiences, RetrievedProjects, OfferExtraction, UserProfile
from sqlmodel import select
from .models import Alice
from .latex_renderer import LaTeXRenderer
from  core.prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)



class GenerationService:
    def __init__(
        self,
        Client: Mistral,
        model: str ,
        renderer: Optional[LaTeXRenderer] = None,
    ):
        self.renderer = renderer or LaTeXRenderer()
        self.client = Client
        self.model = model

    async def generate_cv(
        self,
        username: str,
        session: AsyncSession,
        offer_extraction: OfferExtraction,
        best_experiences: RetrievedExperiences,
        best_projects: RetrievedProjects,
    ) -> str:
        user_result = await session.execute(select(Alice).where(Alice.name == username))
        user = user_result.scalar_one_or_none()
        if user is None:
            raise ValueError(f"No user found for username: {username}")

        user_profile:UserProfile = UserProfile(
            name=user.name,
            education=user.Education,
            number=user.number,
            address=user.adress,
            email_address=user.email_adress,
        )

        _, latex_source = await self.generate_tailored_cv(
            user_profile=user_profile,
            job_offer=offer_extraction,
            retrieved_experiences=best_experiences,
            retrieved_projects=best_projects,
        )
        return latex_source

    async def generate_tailored_cv(
        self,
        user_profile: UserProfile,
        job_offer: OfferExtraction,
        retrieved_experiences: RetrievedExperiences,
        retrieved_projects: RetrievedProjects,
    ) -> tuple[GeneratedCV, str]:
        """
        Executes LLM structured synthesis and deterministically renders to LaTeX.
        Returns: (GeneratedCV, latex_source_string)
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
                response_format=GeneratedCV,
                temperature=0.2, # Low temperature for factual consistency
            )
            
            structured_data: GeneratedCV = response.choices[0].message.parsed
            
            # Deterministic, safe rendering
            latex_source = self.renderer.render(structured_data)
            return structured_data, latex_source

        except Exception as err:
            raise RuntimeError(f"CV Generation Pipeline Error: {err}") from err

    def _assemble_prompt(
        self,
        user: UserProfile,
        offer: OfferExtraction,
        experiences: RetrievedExperiences,
        projects: RetrievedProjects,
    ) -> str:
        return f"""### TARGET JOB DESCRIPTION
{json.dumps(offer.model_dump(), indent=2)}

### CANDIDATE BASE PROFILE
{json.dumps(user.model_dump(), indent=2)}

### RETRIEVED RELEVANT EXPERIENCES (RAG)
{json.dumps(experiences.model_dump(), indent=2)}

### RETRIEVED RELEVANT PROJECTS (RAG)
{json.dumps(projects.model_dump(), indent=2)}

Synthesize this data into the required structured CV output. Prioritize high-relevance matches for the target role."""

