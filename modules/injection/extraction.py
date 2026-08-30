import io
import json
from uuid import UUID
from typing import Dict, List
import uuid
from pypdf import PdfReader
from sqlalchemy.orm import Session
from modules.core.llm import Llm  # Imports configured OpenAI / Claude / Gemini client
from modules.core.database import experience, project  # Target DB models
from modules.injection.schema import ExtractionLLMResponse, ExperienceItem, ProjectItem
from modules.core.security import Settings


class InjectionService:
    def __init__(self, llm_client: Llm):
        self.llm_client = llm_client
    # standardizing llm mistralling initialization for different operations
    @staticmethod
    async def extract_text_from_pdf(file_bytes: bytes) -> str:
        """Extracts plain text from raw PDF bytes."""
        reader = PdfReader(io.BytesIO(file_bytes))
        full_text = []
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                full_text.append(extracted)
        return "\n".join(full_text).strip()

    async def extract_entities_with_llm(self, cv_text: str) -> ExtractionLLMResponse:
        """Invokes LLM with strict JSON schema instructions to extract experiences and projects."""
        client = self.llm_client

        system_prompt = (
            "You are an expert ATS document parser. Extract all professional experiences and projects "
            "from the CV text. For experiences, format title as 'Job Title | Company | Dates' and content as detailed responsibilities and achievements"
            "from the CV text. For projects, format title as 'Project Name | Dates' and content as detailed description and tech stack. Return valid JSON matching the schema strictly."
            "ensure content is a string for each project or ecperience in ecperiences and projects"
        )

        user_prompt = f"CV TEXT:\n\"\"\"\n{cv_text}\n\"\"\"\n\nExtract experiences and projects into JSON."

        # Structured output call (compatible with OpenAI / LangChain wrapper)
        response = client.get_llm_client().chat.complete(
            model=client.handlel_llm(),
            response_format={"type": "json_object"},
            temperature=0.0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        raw_json = response.choices[0].message.content
        parsed = json.loads(raw_json)
        return ExtractionLLMResponse(**parsed)

    @staticmethod
    async def insert_extracted_records(
        db: Session,
        user_id: UUID,
        experiences: List[ExperienceItem],
        projects: List[ProjectItem],
    ) -> Dict[str, int]:
        """Performs low-latency batch insertions for extracted experiences and projects."""
        try:
            # 1. Prepare bulk objects
            exp_records = [
                experience(
                    id = uuid.uuid4(),
                    user_id=user_id,
                    title=item.title,
                    content=item.content,
                )
                for item in experiences
            ]

            proj_records = [
                project(
                    id=uuid.uuid4(),
                    user_id=user_id,
                    title=item.title,
                    content=item.content,
                )
                for item in projects
            ]

            # 2. Add all and commit in a single transaction
            if exp_records:
                db.add_all(exp_records)
            if proj_records:
                db.add_all(proj_records)

            await db.commit()

            return {
                "experiences_inserted": len(exp_records),
                "projects_inserted": len(proj_records),
            }
        except Exception:
            await db.rollback()
            raise


async def async_persist_task(
    db_factory,
    user_id: UUID,
    experiences: List[Dict[str, str]],
    projects: List[Dict[str, str]],
):
    """Background worker function to execute low-latency DB commits out-of-band."""
    db = db_factory
    try:
        exp_items = [ExperienceItem(**e) for e in experiences]
        proj_items = [ProjectItem(**p) for p in projects]
        await InjectionService.insert_extracted_records(db, user_id, exp_items, proj_items)
    finally:
        await db.close()