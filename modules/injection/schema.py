from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class ExperienceItem(BaseModel):
    title: str = Field(..., description="Job title + duration/dates + company name if applicable")
    content: str = Field(..., description="Detailed impact bullet points or responsibilities")


class ProjectItem(BaseModel):
    title: str = Field(..., description="Project name + duration/dates")
    content: str = Field(..., description="Technologies used and project description")


class ExtractionLLMResponse(BaseModel):
    experiences: List[ExperienceItem] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list)


class BulkInsertionPayload(BaseModel):
    experiences: List[ExperienceItem] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list)


class ExtractionResponse(BaseModel):
    status: str
    experiences_count: int
    projects_count: int
    data: ExtractionLLMResponse