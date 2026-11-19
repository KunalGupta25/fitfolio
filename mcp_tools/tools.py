import aiosqlite
from pathlib import Path
from fastmcp import FastMCP
from core.config import settings
from services import jd_analyzer, skill_validator, resume_builder

mcp = FastMCP("fitFolio")


async def _get_db():
    db = await aiosqlite.connect(settings.database_url)
    db.row_factory = aiosqlite.Row
    return db


@mcp.tool()
async def get_full_profile() -> dict:
    """Returns all profile data: personal info, summary, skills,
    projects (with bullets), experience (with bullets), education, certifications."""
    db = await _get_db()
    try:
        profile = await resume_builder.get_full_profile_from_db(db)
        return profile
    finally:
        await db.close()


@mcp.tool()
async def get_skills(validated_only: bool = False) -> list[dict]:
    """Returns skills with name, category, confidence, validated status, and test_score.
    Set validated_only=True to exclude self-reported or failed skills."""
    db = await _get_db()
    try:
        query = """SELECT s.*, c.name as category_name
                   FROM skills s
                   LEFT JOIN skill_categories c ON s.category_id = c.id"""
        if validated_only:
            query += " WHERE s.validated = 1"
        query += " ORDER BY c.display_order ASC, s.name ASC"

        async with db.execute(query) as c:
            rows = await c.fetchall()
            return [dict(r) for r in rows]
    finally:
        await db.close()


@mcp.tool()
async def get_projects(limit: int | None = None) -> list[dict]:
    """Returns active projects with all their bullets and comma-separated keywords."""
    db = await _get_db()
    try:
        query = "SELECT * FROM projects WHERE is_active = 1 ORDER BY display_order ASC"
        if limit:
            query += f" LIMIT {limit}"
        async with db.execute(query) as c:
            proj_rows = await c.fetchall()

        projects = []
        for pr in proj_rows:
            p_dict = dict(pr)
            async with db.execute(
                "SELECT * FROM project_bullets WHERE project_id = ? ORDER BY display_order ASC",
                (p_dict["id"],),
            ) as bc:
                b_rows = await bc.fetchall()
                p_dict["bullets"] = [dict(b) for b in b_rows]
            projects.append(p_dict)
        return projects
    finally:
        await db.close()


@mcp.tool()
async def analyze_jd(jd_text: str) -> dict:
    """Extracts from a job description:
    - required_skills: must-have skills
    - preferred_skills: nice-to-have skills
    - role_keywords: key technical terms for ATS optimization
    - seniority: fresher / junior / mid / senior"""
    return await jd_analyzer.analyze(jd_text)


@mcp.tool()
async def get_relevant_sections(jd_text: str) -> dict:
    """Scores projects, experience, and skills against the JD.
    Returns ranked lists of profile items with relevance scores."""
    db = await _get_db()
    try:
        profile = await resume_builder.get_full_profile_from_db(db)
        analysis = await jd_analyzer.analyze(jd_text)

        all_keywords = set(k.lower() for k in analysis.get("role_keywords", []))
        all_keywords.update(s.lower() for s in analysis.get("required_skills", []))

        # Score projects
        scored_projects = []
        for p in profile.get("projects", []):
            text_corpus = f"{p.get('name', '')} {p.get('tag', '')} " + " ".join(
                f"{b.get('bullet', '')} {b.get('keywords', '')}" for b in p.get("bullets", [])
            ).lower()
            matches = [kw for kw in all_keywords if kw in text_corpus]
            score = round(len(matches) / max(len(all_keywords), 1), 2)
            scored_projects.append({"project": p, "score": score, "matched_keywords": matches})
        scored_projects.sort(key=lambda x: x["score"], reverse=True)

        return {
            "analysis": analysis,
            "ranked_projects": scored_projects,
            "total_skills": len(profile.get("skills", [])),
        }
    finally:
        await db.close()


@mcp.tool()
async def start_validation_test(skill_name: str) -> list[dict]:
    """Generates 3-4 validation questions for a single skill.
    Returns: list of {question, aspect} objects."""
    return await skill_validator.generate_single_test(skill_name)


@mcp.tool()
async def submit_validation_answers(skill_name: str, answers: list[str]) -> dict:
    """Grades answers via Gemini, stores score, and updates validated status in DB.
    Returns: {score, passed, feedback}."""
    db = await _get_db()
    try:
        # Find skill id if exists
        async with db.execute("SELECT id FROM skills WHERE name = ? COLLATE NOCASE", (skill_name,)) as c:
            row = await c.fetchone()
            skill_id = row["id"] if row else 0

        return await skill_validator.grade_and_store(skill_name, answers, skill_id, db)
    finally:
        await db.close()


@mcp.tool()
async def start_bulk_validation_test(skill_names: list[str]) -> dict:
    """Picks top 3 hardest skills from list, generates a combined test.
    Returns: {selected_skills, questions}."""
    return await skill_validator.generate_bulk_test(skill_names)


@mcp.tool()
async def generate_resume_latex(jd_text: str, max_pages: int = 2) -> str:
    """Fills the LaTeX template section by section based on profile data
    and JD relevance. Returns a complete compilable .tex string."""
    db = await _get_db()
    try:
        return await resume_builder.build(jd_text, max_pages, db)
    finally:
        await db.close()


@mcp.tool()
async def log_resume_session(
    jd_role: str, jd_company: str, jd_text: str, output_path: str
) -> int:
    """Saves this resume generation session to history. Returns session_id."""
    db = await _get_db()
    try:
        await db.execute(
            """INSERT INTO resume_sessions (jd_text, jd_role, jd_company, output_path)
               VALUES (?, ?, ?, ?)""",
            (jd_text, jd_role, jd_company, output_path),
        )
        await db.commit()
        async with db.execute("SELECT last_insert_rowid() as lid") as c:
            row = await c.fetchone()
            return row["lid"] if row else 0
    finally:
        await db.close()


@mcp.prompt()
def fill_resume_instructions() -> str:
    return """
    You are filling a LaTeX resume for fitFolio. These rules are non-negotiable:

    1. Only replace <<PLACEHOLDER>> blocks. Never add new \\section{} calls.
    2. Only use skills and content the user has explicitly provided in their profile.
    3. Prioritize validated skills (validated=1) over self-reported (validated=0).
    4. Rewrite the SUMMARY specifically for the target JD keywords.
    5. If a required JD skill is absent from the profile, skip it. Never fabricate.
    6. Priority when trimming for page limit:
       JD-matched projects > validated skills > education > experience > certs > self-reported skills
    7. Each project bullet must start with a strong action verb.
    8. Quantify only where the user has already provided numbers.
    9. Never use: passionate, innovative, leverage, cutting-edge, seamless, dynamic.
    """


@mcp.resource("fitfolio://template")
async def get_latex_template() -> str:
    """The LaTeX template with <<PLACEHOLDER>> blocks."""
    tmpl_path = Path("latex/template.tex")
    if not tmpl_path.exists():
        tmpl_path = Path(__file__).resolve().parent.parent / "latex" / "template.tex"
    with open(tmpl_path, "r", encoding="utf-8") as f:
        return f.read()


@mcp.resource("fitfolio://schema")
async def get_schema_reference() -> str:
    """Field descriptions for all profile data."""
    return """
    personal_info: full_name, phone, email, linkedin (handle), github (handle),
                   portfolio (full URL), city, state
    skills: name, confidence (expert/proficient/familiar),
            validated (1=tested+passed, 0=self-reported, -1=failed),
            evidence (free text describing what they built with it)
    projects: name, tag (subtitle), live_url, github_url, start_date, end_date
    project_bullets: bullet (raw), keywords (comma-separated tech terms)
    experience: role, organization, location, start_date, end_date
    experience_bullets: bullet (raw), keywords
    education: institution, degree, specialization, cgpa, start_date, end_date, location
    certifications: name, issuer, issued_date
    """
