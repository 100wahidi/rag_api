from pydantic import BaseModel

class ExtractionSchema(BaseModel):
    title: str
    required_experiences: list[str]
    domains: list[str]
    technical_skills: list[str]
    non_technical_skills: list[str]
    motivations: list[str]
    keywords: list[str]