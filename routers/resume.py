import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
import aiosqlite
from core.database import get_db
from core.config import settings
from core.templates import render_template
from services import jd_analyzer, resume_builder, tectonic

router = APIRouter(prefix="/resume")


@router.get("/")
async def resume_page(request: Request, db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute("SELECT * FROM resume_sessions ORDER BY created_at DESC") as c:
        rows = await c.fetchall()
    sessions = [dict(r) for r in rows]

    if "text/html" in request.headers.get("accept", ""):
        return render_template(
            request=request,
            name="resume.html",
            context={"sessions": sessions},
        )

    return sessions


@router.post("/analyze-jd")
async def analyze_jd(request: Request, db: aiosqlite.Connection = Depends(get_db)):
    if request.headers.get("content-type", "").startswith("application/json"):
        data = await request.json()
    else:
        form = await request.form()
        data = dict(form)

    jd_text: str = data.get("jd_text", "").strip()
    jd_role: str = data.get("jd_role", "").strip()
    jd_company: str = data.get("jd_company", "").strip()
    max_pages: int = int(data.get("max_pages", 2))

    if not jd_text:
        raise HTTPException(status_code=400, detail="jd_text is required")

    analysis = await jd_analyzer.analyze(jd_text)

    # Score profile sections against JD keywords
    async with db.execute("SELECT name FROM skills WHERE validated = 1") as c:
        validated_skills = [row["name"].lower() for row in await c.fetchall()]
    async with db.execute("SELECT name FROM skills") as c:
        all_skills = [row["name"].lower() for row in await c.fetchall()]

    required = analysis.get("required_skills", [])
    preferred = analysis.get("preferred_skills", [])

    scored_required = [
        {
            "skill": s,
            "in_profile": any(s.lower() == ask or s.lower() in ask for ask in all_skills),
            "validated": any(s.lower() == vsk or s.lower() in vsk for vsk in validated_skills),
        }
        for s in required
    ]
    scored_preferred = [
        {
            "skill": s,
            "in_profile": any(s.lower() == ask or s.lower() in ask for ask in all_skills),
            "validated": any(s.lower() == vsk or s.lower() in vsk for vsk in validated_skills),
        }
        for s in preferred
    ]

    context = {
        "analysis": analysis,
        "scored_required": scored_required,
        "scored_preferred": scored_preferred,
        "role_keywords": analysis.get("role_keywords", []),
        "seniority": analysis.get("seniority", "fresher"),
        "jd_text": jd_text,
        "jd_role": jd_role,
        "jd_company": jd_company,
        "max_pages": max_pages,
    }

    if request.headers.get("hx-request") or "text/html" in request.headers.get("accept", ""):
        return render_template(
            request=request,
            name="partials/jd_analysis.html",
            context=context,
        )

    return {
        "analysis": analysis,
        "scored_required": scored_required,
        "scored_preferred": scored_preferred,
    }


@router.post("/generate")
async def generate_resume(request: Request, db: aiosqlite.Connection = Depends(get_db)):
    if request.headers.get("content-type", "").startswith("application/json"):
        data = await request.json()
    else:
        form = await request.form()
        data = dict(form)

    jd_text: str = data.get("jd_text", "").strip()
    max_pages: int = int(data.get("max_pages", 2))
    jd_role: str = data.get("jd_role", "").strip()
    jd_company: str = data.get("jd_company", "").strip()

    tex_content = await resume_builder.build(jd_text, max_pages, db)

    try:
        session_id, output_path = await tectonic.compile_latex(tex_content)
    except Exception:
        import uuid
        session_id = uuid.uuid4().hex[:8]
        out_dir = Path(settings.output_dir) / session_id
        out_dir.mkdir(parents=True, exist_ok=True)
        tex_file = out_dir / "resume.tex"
        tex_file.write_text(tex_content, encoding="utf-8")
        output_path = str(tex_file)

    await db.execute(
        """INSERT INTO resume_sessions (jd_text, jd_role, jd_company, output_path)
           VALUES (?, ?, ?, ?)""",
        (jd_text, jd_role, jd_company, output_path),
    )
    await db.commit()

    context = {
        "session_id": session_id,
        "download_url": f"/resume/download/{session_id}",
        "tex_content": tex_content,
    }

    if request.headers.get("hx-request") or "text/html" in request.headers.get("accept", ""):
        return render_template(
            request=request,
            name="partials/resume_preview.html",
            context=context,
        )

    return {
        "session_id": session_id,
        "download_url": f"/resume/download/{session_id}",
        "tex_content": tex_content,
    }


@router.get("/download/{session_id}")
async def download_resume(session_id: str):
    pdf_path = os.path.join(settings.output_dir, session_id, "resume.pdf")
    tex_path = os.path.join(settings.output_dir, session_id, "resume.tex")

    if os.path.exists(pdf_path):
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=f"resume_{session_id}.pdf",
        )
    elif os.path.exists(tex_path):
        return FileResponse(
            path=tex_path,
            media_type="text/plain",
            filename=f"resume_{session_id}.tex",
        )
    else:
        raise HTTPException(status_code=404, detail="Resume build artifacts not found.")


@router.get("/history")
async def resume_history(db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute("SELECT * FROM resume_sessions ORDER BY created_at DESC") as c:
        rows = await c.fetchall()
    return [dict(r) for r in rows]
