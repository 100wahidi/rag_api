import json
import logging
from typing import Optional
from uuid import UUID

from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.core.llm import GroqProvider
from modules.core.models import Alice  # Renamed from Alice
from modules.core.prompts import SYSTEM_PROMPT
from modules.generation.latex_renderer import LaTeXRenderer
from modules.generation.schema import (
    GeneratedCV,
    OfferExtraction,
    RetrievedExperiences,
    RetrievedProjects,
    UserProfile,
)

logger = logging.getLogger(__name__)


class GenerationService:
    def __init__(
        self,
        client: GroqProvider,
        renderer: Optional[LaTeXRenderer] = None,
    ):
        self.client = client
        self.renderer = renderer or LaTeXRenderer()

    async def generate_cv_for_user(
        self,
        user_id: UUID,
        session: AsyncSession,
        offer_extraction: OfferExtraction,
        best_experiences: RetrievedExperiences,
        best_projects: RetrievedProjects,
    ) -> tuple[GeneratedCV, str]:
        # Index-driven deterministic query on primary key
        stmt = select(Alice).where(Alice.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user is None:
            raise ValueError(f"User profile not found for ID: {user_id}")

        user_profile = UserProfile(
            name=user.name,
            education=user.education,
            number=user.number,
            address=user.address,
            email_address=user.email_address,
        )

        return await self.generate_tailored_cv(
            user_profile=user_profile,
            job_offer=offer_extraction,
            retrieved_experiences=best_experiences,
            retrieved_projects=best_projects,
        )

    async def generate_tailored_cv(
        self,
        user_profile: UserProfile,
        job_offer: OfferExtraction,
        retrieved_experiences: RetrievedExperiences,
        retrieved_projects: RetrievedProjects,
    ) -> tuple[GeneratedCV, str]:
        payload = self._assemble_prompt(
            user=user_profile,
            offer=job_offer,
            experiences=retrieved_experiences,
            projects=retrieved_projects,
        )

        structured_cv = await self.client.generate_structured(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=payload,
            response_format=GeneratedCV,
        )

        try:
            latex_source = self.renderer.render(structured_cv)
        except Exception as exc:
            logger.error("Template rendering failed for CV schema", exc_info=True)
            raise RuntimeError(f"LaTeX rendering failure: {exc}") from exc

        return structured_cv, latex_source

    @staticmethod
    def _assemble_prompt(
        user: UserProfile,
        offer: OfferExtraction,
        experiences: RetrievedExperiences,
        projects: RetrievedProjects,
    ) -> str:
        return (
            "### TARGET JOB DESCRIPTION\n"
            f"{json.dumps(offer.model_dump(), indent=2)}\n\n"
            "### CANDIDATE BASE PROFILE\n"
            f"{json.dumps(user.model_dump(), indent=2)}\n\n"
            "### RETRIEVED RELEVANT EXPERIENCES (RAG)\n"
            f"{json.dumps(experiences.model_dump(), indent=2)}\n\n"
            "### RETRIEVED RELEVANT PROJECTS (RAG)\n"
            f"{json.dumps(projects.model_dump(), indent=2)}\n\n"
            "Synthesize this data into the required structured CV output.\n"
            "Prioritize high-relevance matches for the target role."
        )
