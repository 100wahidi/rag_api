from enum import StrEnum
from typing import List
from pydantic import BaseModel, ConfigDict, Field


class ExperienceItem(BaseModel):
    title: str
    content: str

class RetrievedExperiences(BaseModel):
    experiences: List[ExperienceItem] = Field(default_factory=list)

class ProjectItem(BaseModel):
    title: str
    content: str = Field(default_factory=list, description="Key features, architecture, and impact")

class RetrievedProjects(BaseModel):
    projects: List[ProjectItem] = Field(default_factory=list)

class RetrievalTarget(StrEnum):
    EXPERIENCES = "experiences"
    PROJECTS = "projects"


class RetrievedItemDTO(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    similarity_score: float = Field(..., ge=0.0, le=1.0)

class ExtractedExperience(BaseModel):
    retrieved_experiences: List[str] = Field(default_factory=list)

class ExtractedSkills(BaseModel):
    retrieved_skills: List[str] = Field(default_factory=list)

