from typing import List
from pydantic import BaseModel, Field


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


