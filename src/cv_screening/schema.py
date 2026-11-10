"""Schema ekstraksi. Sengaja TIDAK memuat usia, gender, agama, status pernikahan, etnis, atau foto."""
from typing import Optional

from pydantic import BaseModel


class Experience(BaseModel):
    company: str
    title: str
    start: Optional[str] = None   # 'YYYY-MM' atau 'YYYY' jika hanya tahun
    end: Optional[str] = None     # 'YYYY-MM', 'YYYY', atau 'present'
    highlights: list[str] = []
    evidence: str                 # kutipan persis dari CV


class Education(BaseModel):
    institution: str
    degree: Optional[str] = None
    field: Optional[str] = None
    end_year: Optional[int] = None
    evidence: str


class Skill(BaseModel):
    name: str
    evidence: str


class CandidateProfile(BaseModel):
    full_name: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    education: list[Education] = []
    experience: list[Experience] = []
    skills: list[Skill] = []
    extraction_notes: list[str] = []   # hal ambigu yang dicatat extractor
