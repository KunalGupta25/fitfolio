from __future__ import annotations

from pydantic import BaseModel


# ── Personal Info ──────────────────────────────────────────────────────────────

class PersonalInfoUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    email: str | None = None
    linkedin: str | None = None
    github: str | None = None
    portfolio: str | None = None
    city: str | None = None
    state: str | None = None


# ── Summary ────────────────────────────────────────────────────────────────────

class SummaryUpdate(BaseModel):
    raw_bio: str


# ── Education ──────────────────────────────────────────────────────────────────

class EducationCreate(BaseModel):
    institution: str
    degree: str
    specialization: str | None = None
    cgpa: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    location: str | None = None
    display_order: int = 0


class EducationUpdate(BaseModel):
    institution: str | None = None
    degree: str | None = None
    specialization: str | None = None
    cgpa: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    location: str | None = None
    display_order: int | None = None


class EducationResponse(BaseModel):
    id: int
    institution: str
    degree: str
    specialization: str | None = None
    cgpa: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    location: str | None = None
    display_order: int = 0


# ── Skill Categories ───────────────────────────────────────────────────────────

class SkillCategoryCreate(BaseModel):
    name: str
    display_order: int = 0


class SkillCategoryResponse(BaseModel):
    id: int
    name: str
    display_order: int = 0


# ── Skills ─────────────────────────────────────────────────────────────────────

class SkillCreate(BaseModel):
    name: str
    category_id: int | None = None
    confidence: str = "proficient"
    evidence: str | None = None


class SkillUpdate(BaseModel):
    name: str | None = None
    category_id: int | None = None
    confidence: str | None = None
    validated: int | None = None
    test_score: float | None = None
    evidence: str | None = None


class SkillResponse(BaseModel):
    id: int
    name: str
    category_id: int | None = None
    confidence: str
    validated: int
    test_score: float | None = None
    evidence: str | None = None


# ── Projects ───────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str
    tag: str | None = None
    live_url: str | None = None
    github_url: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    display_order: int = 0
    is_active: int = 1


class ProjectUpdate(BaseModel):
    name: str | None = None
    tag: str | None = None
    live_url: str | None = None
    github_url: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    display_order: int | None = None
    is_active: int | None = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    tag: str | None = None
    live_url: str | None = None
    github_url: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    display_order: int = 0
    is_active: int = 1


# ── Bullets ────────────────────────────────────────────────────────────────────

class BulletCreate(BaseModel):
    bullet: str
    keywords: str | None = None
    display_order: int = 0


class BulletUpdate(BaseModel):
    bullet: str | None = None
    keywords: str | None = None
    display_order: int | None = None


class BulletResponse(BaseModel):
    id: int
    bullet: str
    keywords: str | None = None
    display_order: int = 0


# ── Experience ─────────────────────────────────────────────────────────────────

class ExperienceCreate(BaseModel):
    role: str
    organization: str
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    display_order: int = 0


class ExperienceUpdate(BaseModel):
    role: str | None = None
    organization: str | None = None
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    display_order: int | None = None


class ExperienceResponse(BaseModel):
    id: int
    role: str
    organization: str
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    display_order: int = 0


# ── Certifications ─────────────────────────────────────────────────────────────

class CertificationCreate(BaseModel):
    name: str
    issuer: str
    issued_date: str | None = None
    url: str | None = None
    display_order: int = 0


class CertificationResponse(BaseModel):
    id: int
    name: str
    issuer: str
    issued_date: str | None = None
    url: str | None = None
    display_order: int = 0


# ── Validation ─────────────────────────────────────────────────────────────────

class ValidationTestResponse(BaseModel):
    questions: list[dict]


class ValidationSubmit(BaseModel):
    answers: list[str]


class ValidationResult(BaseModel):
    score: float
    passed: bool
    feedback: str


# ── JD Analysis ────────────────────────────────────────────────────────────────

class JDAnalysis(BaseModel):
    required_skills: list[str]
    preferred_skills: list[str]
    role_keywords: list[str]
    seniority: str


# ── Resume Generation ──────────────────────────────────────────────────────────

class ResumeGenerateRequest(BaseModel):
    jd_text: str
    jd_role: str = ""
    jd_company: str = ""
    max_pages: int = 2


class ResumeSessionResponse(BaseModel):
    id: int
    jd_text: str | None = None
    jd_role: str | None = None
    jd_company: str | None = None
    output_path: str | None = None
    created_at: str | None = None
