from typing import List

from pydantic import BaseModel


class ExperienceItem(BaseModel):
	title: str
	description: str


class ProjectItem(BaseModel):
	title: str
	description: str


class GeneratedCV(BaseModel):
	profile: str
	experiences: List[ExperienceItem] = []
	projects: List[ProjectItem] = []