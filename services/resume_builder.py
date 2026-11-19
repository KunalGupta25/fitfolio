import os
import aiosqlite
from pathlib import Path
from services import jd_analyzer
from services.gemini import call_gemini


def sanitize_latex(text: str) -> str:
    """Escapes special LaTeX characters in user-provided text."""
    if not text:
        return ""
    # Map of special characters that need escaping
    chars = {
        "\\": "\\textbackslash{}",
        "&": "\\&",
        "%": "\\%",
        "$": "\\$",
        "#": "\\#",
        "_": "\\_",
        "{": "\\{",
        "}": "\\}",
        "~": "\\textasciitilde{}",
        "^": "\\textasciicircum{}",
    }
    # Don't replace if it's already LaTeX formatting
    result = []
    i = 0
    while i < len(text):
        c = text[i]
        if c in chars and (i == 0 or text[i - 1] != "\\"):
            result.append(chars[c])
        else:
            result.append(c)
        i += 1
    return "".join(result)


async def get_full_profile_from_db(db: aiosqlite.Connection) -> dict:
    profile = {}

    # Personal info
    async with db.execute("SELECT * FROM personal_info WHERE id = 1") as c:
        row = await c.fetchone()
        profile["personal_info"] = dict(row) if row else {}

    # Summary
    async with db.execute("SELECT * FROM summary WHERE id = 1") as c:
        row = await c.fetchone()
        profile["summary"] = dict(row) if row else {"raw_bio": ""}

    # Education
    async with db.execute("SELECT * FROM education ORDER BY display_order ASC") as c:
        rows = await c.fetchall()
        profile["education"] = [dict(r) for r in rows]

    # Skills with categories
    async with db.execute(
        """SELECT s.*, c.name as category_name, c.display_order as cat_order
           FROM skills s
           LEFT JOIN skill_categories c ON s.category_id = c.id
           ORDER BY c.display_order ASC, s.validated DESC, s.name ASC"""
    ) as c:
        rows = await c.fetchall()
        profile["skills"] = [dict(r) for r in rows]

    # Projects with bullets
    async with db.execute("SELECT * FROM projects WHERE is_active = 1 ORDER BY display_order ASC") as c:
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
        profile["projects"] = projects

    # Experience with bullets
    async with db.execute("SELECT * FROM experience ORDER BY display_order ASC") as c:
        exp_rows = await c.fetchall()
        experiences = []
        for er in exp_rows:
            e_dict = dict(er)
            async with db.execute(
                "SELECT * FROM experience_bullets WHERE experience_id = ? ORDER BY display_order ASC",
                (e_dict["id"],),
            ) as bc:
                b_rows = await bc.fetchall()
                e_dict["bullets"] = [dict(b) for b in b_rows]
            experiences.append(e_dict)
        profile["experience"] = experiences

    # Certifications
    async with db.execute("SELECT * FROM certifications ORDER BY display_order ASC") as c:
        rows = await c.fetchall()
        profile["certifications"] = [dict(r) for r in rows]

    return profile


def build_heading(p: dict) -> str:
    name = p.get("full_name") or "Your Name"
    phone = p.get("phone") or ""
    email = p.get("email") or ""
    linkedin = p.get("linkedin") or ""
    github = p.get("github") or ""
    portfolio = p.get("portfolio") or ""
    city = p.get("city") or ""
    state = p.get("state") or ""

    location = f"{city}, {state}".strip(", ")

    parts = []
    if phone:
        parts.append(f"\\texttt{{{sanitize_latex(phone)}}}")
    if email:
        parts.append(f"\\texttt{{{sanitize_latex(email)}}}")
    if linkedin:
        li_handle = linkedin.removeprefix("https://linkedin.com/in/").removeprefix("linkedin.com/in/")
        parts.append(f"\\href{{https://linkedin.com/in/{li_handle}}}{{\\texttt{{linkedin/{sanitize_latex(li_handle)}}}}}")
    if github:
        gh_handle = github.removeprefix("https://github.com/").removeprefix("github.com/")
        parts.append(f"\\href{{https://github.com/{gh_handle}}}{{\\texttt{{github/{sanitize_latex(gh_handle)}}}}}")
    if portfolio:
        disp_url = portfolio.removeprefix("https://").removeprefix("http://").rstrip("/")
        parts.append(f"\\href{{{portfolio}}}{{\\texttt{{{sanitize_latex(disp_url)}}}}}")

    contact_line = " \\hspace{1pt} $|$ \\hspace{1pt} ".join(parts)
    loc_line = f"\\\\ \\vspace{{2pt}}\n    \\small \\texttt{{{sanitize_latex(location)}}}" if location else ""

    return f"""\\begin{{center}}
    \\textbf{{\\Huge {sanitize_latex(name)}}} \\\\ \\vspace{{4pt}}
    \\small {contact_line}
    {loc_line}
    \\\\ \\vspace{{-3pt}}
\\end{{center}}"""


async def build_summary(raw_bio: str, jd_data: dict) -> str:
    if not raw_bio:
        return "Dedicated software developer with hands-on project experience seeking to contribute technical skills to engineering initiatives."

    role_keywords = ", ".join(jd_data.get("role_keywords", []))
    seniority = jd_data.get("seniority", "fresher")

    prompt = f"""Rewrite this candidate's raw professional bio into a tailored, impactful 2-3 sentence resume summary for a {seniority} level role.
Target role keywords for context: {role_keywords}

Rules:
1. ONLY reference skills, technologies, and achievements present in the candidate's raw bio.
2. DO NOT assume or invent skills they did not mention.
3. No fluffy buzzwords (avoid: passionate, innovative, cutting-edge, leverage, synergy).
4. Omit first-person pronouns (no "I", "me", "my").
5. Format key technologies or domains in bold using LaTeX \\textbf{{...}}.

Candidate Raw Bio:
{raw_bio}

Return ONLY the summary text in valid LaTeX."""

    try:
        rewritten = await call_gemini(prompt)
        cleaned = rewritten.strip().removeprefix("```latex").removeprefix("```").removesuffix("```").strip()
        return cleaned
    except Exception:
        # Fallback to sanitized raw bio if AI call fails
        return sanitize_latex(raw_bio)


def build_education(education_list: list[dict]) -> str:
    if not education_list:
        return ""
    blocks = []
    for edu in education_list:
        inst = sanitize_latex(edu.get("institution", ""))
        deg = sanitize_latex(edu.get("degree", ""))
        spec = edu.get("specialization", "")
        if spec:
            deg += f" in {sanitize_latex(spec)}"
        cgpa = edu.get("cgpa", "")
        if cgpa:
            deg += f" $|$ \\textbf{{CGPA: {sanitize_latex(cgpa)}}}"

        dates = sanitize_latex(f"{edu.get('start_date', '')} -- {edu.get('end_date', '')}".strip(" -"))
        loc = sanitize_latex(edu.get("location", ""))

        blocks.append(f"""    \\resumeSubheading
      {{{inst}}}{{{dates}}}
      {{{deg}}}{{{loc}}}""")
    return "\n".join(blocks)


def build_skills(skills_list: list[dict], required_skills: list[str]) -> str:
    if not skills_list:
        return ""

    # Group skills by category
    categories: dict[str, list[dict]] = {}
    for s in skills_list:
        cat = s.get("category_name") or "Core Technologies"
        categories.setdefault(cat, []).append(s)

    lines = []
    for cat_name, cat_skills in categories.items():
        # Sort skills: validated first, then by matching required_skills
        sorted_skills = sorted(
            cat_skills,
            key=lambda x: (
                x.get("validated", 0) == 1,
                any(req.lower() in x.get("name", "").lower() for req in required_skills),
            ),
            reverse=True,
        )
        skill_names = [sanitize_latex(s.get("name", "")) for s in sorted_skills]
        if skill_names:
            line = f"     \\textbf{{{sanitize_latex(cat_name)}}} {{: {', '.join(skill_names)}}} \\\\"
            lines.append(line)

    return "\n".join(lines)


def build_projects(projects_list: list[dict], max_items: int = 3) -> str:
    if not projects_list:
        return ""

    blocks = []
    for proj in projects_list[:max_items]:
        name = sanitize_latex(proj.get("name", ""))
        tag = sanitize_latex(proj.get("tag", ""))
        live_url = proj.get("live_url", "")
        gh_url = proj.get("github_url", "")
        start_d = proj.get("start_date", "")
        end_d = proj.get("end_date", "")
        dates = sanitize_latex(f"{start_d} -- {end_d}".strip(" -"))

        header_parts = [f"\\textbf{{{name}}}"]
        if live_url:
            header_parts.append(f"\\href{{{live_url}}}{{\\textit{{Live Demo}}}}")
        if gh_url:
            header_parts.append(f"\\href{{{gh_url}}}{{\\textit{{GitHub}}}}")
        if tag:
            header_parts.append(tag)

        heading_left = " $|$ ".join(header_parts)

        bullet_items = []
        for b in proj.get("bullets", []):
            b_text = sanitize_latex(b.get("bullet", ""))
            bullet_items.append(f"            \\resumeItem{{{b_text}}}")

        bullets_block = "\n".join(bullet_items) if bullet_items else "            \\resumeItem{Developed core application features and architecture.}"

        blocks.append(f"""      \\resumeProjectHeading
          {{{heading_left}}}{{{dates}}}
          \\resumeItemListStart
{bullets_block}
          \\resumeItemListEnd""")

    return "\n\n".join(blocks)


def build_experience(exp_list: list[dict], max_items: int = 3) -> str:
    if not exp_list:
        return ""

    blocks = []
    for exp in exp_list[:max_items]:
        role = sanitize_latex(exp.get("role", ""))
        org = sanitize_latex(exp.get("organization", ""))
        loc = sanitize_latex(exp.get("location", ""))
        start_d = exp.get("start_date", "")
        end_d = exp.get("end_date", "")
        dates = sanitize_latex(f"{start_d} -- {end_d}".strip(" -"))

        bullet_items = []
        for b in exp.get("bullets", []):
            b_text = sanitize_latex(b.get("bullet", ""))
            bullet_items.append(f"        \\resumeItem{{{b_text}}}")

        bullets_block = "\n".join(bullet_items) if bullet_items else "        \\resumeItem{Contributed to team deliverables and responsibilities.}"

        blocks.append(f"""    \\resumeSubheading
      {{{role}}}{{{dates}}}
      {{{org}}}{{{loc}}}
      \\resumeItemListStart
{bullets_block}
      \\resumeItemListEnd""")

    return "\n".join(blocks)


def build_certs(certs_list: list[dict]) -> str:
    if not certs_list:
        return ""

    lines = []
    for cert in certs_list:
        name = sanitize_latex(cert.get("name", ""))
        issuer = sanitize_latex(cert.get("issuer", ""))
        date = sanitize_latex(cert.get("issued_date", ""))
        details = f"{name} -- {issuer}"
        if date:
            details += f" ({date})"
        lines.append(f"        \\textbf{{{details}}} \\\\")

    return "\n".join(lines)


async def build(jd_text: str, max_pages: int, db: aiosqlite.Connection) -> str:
    # 1. Analyze JD
    jd_data = await jd_analyzer.analyze(jd_text) if jd_text.strip() else {}

    # 2. Get full profile from DB
    profile = await get_full_profile_from_db(db)

    # 3. Build each section
    heading = build_heading(profile.get("personal_info", {}))
    summary = await build_summary(profile.get("summary", {}).get("raw_bio", ""), jd_data)
    education = build_education(profile.get("education", []))
    skills = build_skills(profile.get("skills", []), jd_data.get("required_skills", []))
    
    # Adjust items based on max_pages
    proj_limit = 4 if max_pages > 1 else 2
    exp_limit = 3 if max_pages > 1 else 2

    projects = build_projects(profile.get("projects", []), max_items=proj_limit)
    experience = build_experience(profile.get("experience", []), max_items=exp_limit)
    certs = build_certs(profile.get("certifications", []))

    # 4. Read template and replace placeholders
    template_path = Path("latex/template.tex")
    if not template_path.exists():
        template_path = Path(__file__).resolve().parent.parent / "latex" / "template.tex"

    with open(template_path, "r", encoding="utf-8") as f:
        tex = f.read()

    tex = tex.replace("<<HEADING_BLOCK>>", heading)
    tex = tex.replace("<<SUMMARY_BLOCK>>", summary)
    tex = tex.replace("<<EDUCATION_BLOCK>>", education)
    tex = tex.replace("<<SKILLS_BLOCK>>", skills)
    tex = tex.replace("<<PROJECTS_BLOCK>>", projects)
    tex = tex.replace("<<EXPERIENCE_BLOCK>>", experience)
    tex = tex.replace("<<CERTIFICATIONS_BLOCK>>", certs)

    return tex
