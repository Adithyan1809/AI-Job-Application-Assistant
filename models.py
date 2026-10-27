"""Data models for jobs, applications, and AI summaries."""

import urllib.parse
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any


VALID_STATUSES = ["Interested", "Applied", "Interview", "Offer", "Rejected"]


def get_portal_info(url: str = "", source: str = "") -> Dict[str, str]:
    """Identify the originating job website (LinkedIn, Naukri, Internshala, Glassdoor, etc.)."""
    combined = f"{url} {source}".lower()
    if "linkedin" in combined:
        return {
            "name": "LinkedIn",
            "full_name": "LinkedIn Jobs",
            "icon": "💼",
            "color": "#0077b5",
            "bg": "#f0f7ff",
            "border": "#0077b5",
            "domain": "linkedin.com",
            "tagline": "Professional Network & Live Jobs"
        }
    elif "naukri" in combined:
        return {
            "name": "Naukri",
            "full_name": "Naukri.com",
            "icon": "💼",
            "color": "#16a34a",
            "bg": "#f0fdf4",
            "border": "#16a34a",
            "domain": "naukri.com",
            "tagline": "India's Leading Job Portal"
        }
    elif "internshala" in combined:
        return {
            "name": "Internshala",
            "full_name": "Internshala",
            "icon": "🎓",
            "color": "#0284c7",
            "bg": "#f0f9ff",
            "border": "#0284c7",
            "domain": "internshala.com",
            "tagline": "Fresher Jobs & Internships Platform"
        }
    elif "glassdoor" in combined:
        return {
            "name": "Glassdoor",
            "full_name": "Glassdoor",
            "icon": "🏢",
            "color": "#0caa41",
            "bg": "#eafaf1",
            "border": "#0caa41",
            "domain": "glassdoor.com",
            "tagline": "Company Reviews & Jobs"
        }
    elif "indeed" in combined:
        return {
            "name": "Indeed",
            "full_name": "Indeed",
            "icon": "🔍",
            "color": "#2557a7",
            "bg": "#eef2ff",
            "border": "#2557a7",
            "domain": "indeed.com",
            "tagline": "Global Job Search Engine"
        }
    else:
        domain = "Public Job Portal"
        domain_name = "job-portal"
        try:
            netloc = urllib.parse.urlparse(url).netloc.replace("www.", "")
            if netloc:
                domain = netloc.split(".")[0].capitalize()
                domain_name = netloc
        except Exception:
            pass
        return {
            "name": domain,
            "full_name": domain,
            "icon": "🌐",
            "color": "#475569",
            "bg": "#f8fafc",
            "border": "#94a3b8",
            "domain": domain_name,
            "tagline": "Live Public Listing"
        }


@dataclass
class JobListing:
    """Represents a job listing discovered or extracted via Playwright MCP."""
    title: str
    company: str
    location: str
    experience: str
    description: str
    url: str
    salary: Optional[str] = "Not Specified"
    source: str = "Playwright MCP"
    extracted_via_mcp: bool = True
    id: Optional[int] = None
    created_at: Optional[str] = None

    def __post_init__(self):
        if not self.salary:
            self.salary = "Not Specified"
        if not self.created_at:
            self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @property
    def portal_info(self) -> Dict[str, str]:
        return get_portal_info(self.url, self.source)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JobListing":
        return cls(
            title=data.get("title", "Untitled Position"),
            company=data.get("company", "Unknown Company"),
            location=data.get("location", "Not Specified"),
            experience=data.get("experience", "Not Specified"),
            salary=data.get("salary") or "Not Specified",
            description=data.get("description", ""),
            url=data.get("url", "#"),
            source=data.get("source", "Playwright MCP"),
            extracted_via_mcp=data.get("extracted_via_mcp", True),
            id=data.get("id"),
            created_at=data.get("created_at"),
        )


@dataclass
class Application:
    """Represents a saved job tracked by the student/applicant."""
    title: str
    company: str
    location: str
    experience: str
    description: str
    url: str
    status: str = "Interested"
    salary: Optional[str] = "Not Specified"
    notes: str = ""
    job_id: Optional[int] = None
    id: Optional[int] = None
    saved_at: Optional[str] = None
    updated_at: Optional[str] = None

    def __post_init__(self):
        if self.status not in VALID_STATUSES:
            self.status = "Interested"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not self.saved_at:
            self.saved_at = now
        if not self.updated_at:
            self.updated_at = now

    @property
    def portal_info(self) -> Dict[str, str]:
        return get_portal_info(self.url, "")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Application":
        return cls(
            title=data.get("title", ""),
            company=data.get("company", ""),
            location=data.get("location", ""),
            experience=data.get("experience", ""),
            salary=data.get("salary") or "Not Specified",
            description=data.get("description", ""),
            url=data.get("url", "#"),
            status=data.get("status", "Interested"),
            notes=data.get("notes", ""),
            job_id=data.get("job_id"),
            id=data.get("id"),
            saved_at=data.get("saved_at"),
            updated_at=data.get("updated_at"),
        )


@dataclass
class AISummary:
    """Represents an AI-generated analysis of a job listing."""
    job_title: str
    company: str
    required_skills: List[str] = field(default_factory=list)
    responsibilities: List[str] = field(default_factory=list)
    experience_requirements: str = ""
    prep_advice: List[str] = field(default_factory=list)
    relevance_explanation: str = ""
    is_ai_generated: bool = True
    disclaimer: str = (
        "Note: This summary is generated from the job description for educational "
        "and preparation purposes. No resume was analyzed, so this does not calculate "
        "a personal resume-to-job match."
    )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
