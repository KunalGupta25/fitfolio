from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import aiosqlite
from core.database import init_db, get_db
from core.templates import render_template
from routers import profile, education, skills, projects, experience, certifications, resume


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="fitFolio",
    description="Personal skill-validated resume engine with zero assumptions",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(profile.router, tags=["profile"])
app.include_router(education.router, tags=["education"])
app.include_router(skills.router, tags=["skills"])
app.include_router(projects.router, tags=["projects"])
app.include_router(experience.router, tags=["experience"])
app.include_router(certifications.router, tags=["certifications"])
app.include_router(resume.router, tags=["resume"])


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: aiosqlite.Connection = Depends(get_db)):
    # 1. Fetch completeness data
    async with db.execute("SELECT * FROM personal_info WHERE id = 1") as c:
        pi = await c.fetchone()
    async with db.execute("SELECT * FROM summary WHERE id = 1") as c:
        sm = await c.fetchone()
    async with db.execute("SELECT COUNT(*) as cnt FROM education") as c:
        ed = (await c.fetchone())["cnt"]
    async with db.execute("SELECT COUNT(*) as cnt FROM skills") as c:
        sk_total = (await c.fetchone())["cnt"]
    async with db.execute("SELECT COUNT(*) as cnt FROM skills WHERE validated = 1") as c:
        sk_valid = (await c.fetchone())["cnt"]
    async with db.execute("SELECT COUNT(*) as cnt FROM projects WHERE is_active = 1") as c:
        proj_cnt = (await c.fetchone())["cnt"]
    async with db.execute("SELECT COUNT(*) as cnt FROM certifications") as c:
        cert_cnt = (await c.fetchone())["cnt"]
    async with db.execute(
        """SELECT COUNT(*) as cnt FROM projects p
           WHERE EXISTS (SELECT 1 FROM project_bullets pb WHERE pb.project_id = p.id)"""
    ) as c:
        pb_cnt = (await c.fetchone())["cnt"]

    completeness = {
        "personal_info": pi is not None and bool(pi["full_name"]),
        "summary": sm is not None and bool(sm["raw_bio"]),
        "skills": sk_total >= 3,
        "validated_skill": sk_valid > 0,
        "projects": pb_cnt > 0,
        "education": ed > 0,
    }

    stats = {
        "total_skills": sk_total,
        "validated_skills": sk_valid,
        "projects": proj_cnt,
        "certifications": cert_cnt,
    }

    return render_template(
        request=request,
        name="dashboard.html",
        context={
            "completeness": completeness,
            "stats": stats,
        },
    )


@app.get("/health")
async def health():
    return {"status": "ok", "app": "fitFolio"}
