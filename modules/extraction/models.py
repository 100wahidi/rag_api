from typing import List
from pydantic import BaseModel, Field

class ExractionItem(BaseModel):
    title: str = Field(..., description="Target job position title")
    technical_skills: List[str] = Field(default_factory=list, description="Extracted hard technical skills")
    required_experiences: List[str] = Field(default_factory=list, description="Target missions and experience expectations")
    non_technical_skills: List[str] = Field(default_factory=list, description="Soft skills and organizational attributes")
    motivations: List[str] = Field(default_factory=list, description="Company cultural values and candidate motivations")
    keywords: List[str] = Field(default_factory=list, description="High-frequency ATS keywords")