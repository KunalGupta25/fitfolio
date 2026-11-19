from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
import aiosqlite
from core.database import get_db
from core.templates import render_template

router = APIRouter(prefix="/profile")


@router.get("/")
@router.get("", include_in_schema=False)
async def get_profile(request: Request, db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute("SELECT * FROM personal_info WHERE id = 1") as cursor:
        personal_row = await cursor.fetchone()
    async with db.execute("SELECT * FROM summary WHERE id = 1") as cursor:
        summary_row = await cursor.fetchone()

    p_dict = dict(personal_row) if personal_row else {}
    s_dict = dict(summary_row) if summary_row else {"raw_bio": ""}

    if "text/html" in request.headers.get("accept", ""):
        return render_template(
            request=request,
            name="profile.html",
            context={
                "personal_info": p_dict,
                "summary": s_dict,
                "raw_bio": s_dict.get("raw_bio", ""),
            },
        )

    return {
        "personal_info": p_dict,
        "summary": s_dict,
    }


@router.post("/personal")
async def upsert_personal(request: Request, db: aiosqlite.Connection = Depends(get_db)):
    if request.headers.get("content-type", "").startswith("application/json"):
        data = await request.json()
    else:
        form = await request.form()
        data = dict(form)

    fields = [
        "full_name", "phone", "email", "linkedin",
        "github", "portfolio", "city", "state"
    ]
    values = {f: data.get(f, "") for f in fields}
    await db.execute(
        """INSERT OR REPLACE INTO personal_info
           (id, full_name, phone, email, linkedin, github, portfolio, city, state)
           VALUES (1, :full_name, :phone, :email, :linkedin, :github, :portfolio, :city, :state)""",
        values,
    )
    await db.commit()

    async with db.execute("SELECT * FROM personal_info WHERE id = 1") as cursor:
        row = await cursor.fetchone()
    p_dict = dict(row) if row else {}

    if "text/html" in request.headers.get("accept", "") or request.headers.get("hx-request"):
        return HTMLResponse(
            """<div class="bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs p-3 rounded-md flex items-center justify-between">
                <span>✓ Personal info saved successfully!</span>
                <a href="/profile" class="underline font-medium ml-2">Reload</a>
            </div>"""
        )

    return p_dict


@router.post("/summary")
async def upsert_summary(request: Request, db: aiosqlite.Connection = Depends(get_db)):
    if request.headers.get("content-type", "").startswith("application/json"):
        data = await request.json()
    else:
        form = await request.form()
        data = dict(form)

    raw_bio = data.get("raw_bio", "")
    await db.execute(
        "INSERT OR REPLACE INTO summary (id, raw_bio) VALUES (1, ?)",
        (raw_bio,),
    )
    await db.commit()

    async with db.execute("SELECT * FROM summary WHERE id = 1") as cursor:
        row = await cursor.fetchone()
    s_dict = dict(row) if row else {}

    if "text/html" in request.headers.get("accept", "") or request.headers.get("hx-request"):
        return HTMLResponse(
            """<div class="bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs p-3 rounded-md flex items-center justify-between">
                <span>✓ Professional bio updated!</span>
                <a href="/profile" class="underline font-medium ml-2">Reload</a>
            </div>"""
        )

    return s_dict


@router.get("/completeness")
async def get_completeness(db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute("SELECT * FROM personal_info WHERE id = 1") as c:
        pi = await c.fetchone()
    async with db.execute("SELECT * FROM summary WHERE id = 1") as c:
        sm = await c.fetchone()
    async with db.execute("SELECT COUNT(*) as cnt FROM education") as c:
        ed = await c.fetchone()
    async with db.execute("SELECT COUNT(*) as cnt FROM skills") as c:
        sk = await c.fetchone()
    async with db.execute("SELECT COUNT(*) as cnt FROM skills WHERE validated = 1") as c:
        vsk = await c.fetchone()
    async with db.execute(
        """SELECT COUNT(*) as cnt FROM projects p
           WHERE EXISTS (SELECT 1 FROM project_bullets pb WHERE pb.project_id = p.id)"""
    ) as c:
        pb = await c.fetchone()

    return {
        "personal_info": pi is not None and bool(pi["full_name"]),
        "summary": sm is not None and bool(sm["raw_bio"]),
        "skills": sk["cnt"] >= 3,
        "validated_skill": vsk["cnt"] > 0,
        "projects": pb["cnt"] > 0,
        "education": ed["cnt"] > 0,
    }
