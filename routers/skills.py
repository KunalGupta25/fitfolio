from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import HTMLResponse
import aiosqlite
from core.database import get_db
from core.templates import render_template
from services import skill_validator

router = APIRouter(prefix="/skills")


@router.get("/")
@router.get("", include_in_schema=False)
async def list_skills(request: Request, db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute(
        """SELECT s.*, sc.name as category_name, sc.display_order as cat_order
           FROM skills s
           LEFT JOIN skill_categories sc ON s.category_id = sc.id
           ORDER BY sc.display_order ASC, s.validated DESC, s.name ASC"""
    ) as cursor:
        skill_rows = await cursor.fetchall()
        skills = [dict(r) for r in skill_rows]

    async with db.execute(
        "SELECT * FROM skill_categories ORDER BY display_order ASC"
    ) as cursor:
        cat_rows = await cursor.fetchall()
        categories = [dict(r) for r in cat_rows]

    if "text/html" in request.headers.get("accept", ""):
        return render_template(
            request=request,
            name="skills.html",
            context={
                "skills": skills,
                "categories": categories,
            },
        )

    return skills


@router.get("/categories")
async def list_categories(db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute(
        "SELECT * FROM skill_categories ORDER BY display_order ASC"
    ) as cursor:
        rows = await cursor.fetchall()
    return [dict(r) for r in rows]


@router.post("/categories", status_code=201)
async def create_category(request: Request, db: aiosqlite.Connection = Depends(get_db)):
    if request.headers.get("content-type", "").startswith("application/json"):
        data = await request.json()
    else:
        form = await request.form()
        data = dict(form)

    name = data.get("name", "").strip()
    display_order = int(data.get("display_order", 0))

    await db.execute(
        "INSERT INTO skill_categories (name, display_order) VALUES (?, ?)",
        (name, display_order),
    )
    await db.commit()
    async with db.execute(
        "SELECT * FROM skill_categories WHERE id = last_insert_rowid()"
    ) as c:
        row = await c.fetchone()
    cat_dict = dict(row) if row else {}

    if request.headers.get("hx-request"):
        return HTMLResponse(
            f"""<li class="flex items-center justify-between py-2 text-sm text-slate-700">
                <span>{cat_dict.get('name', '')}</span>
                <button
                  hx-delete="/skills/categories/{cat_dict.get('id', '')}"
                  hx-target="closest li"
                  hx-swap="outerHTML"
                  hx-confirm="Delete category '{cat_dict.get('name', '')}'?"
                  class="text-slate-400 hover:text-red-500 transition-colors text-xs px-1"
                >✕</button>
            </li>"""
        )

    return cat_dict


@router.delete("/categories/{id}", status_code=204)
async def delete_category(id: int, db: aiosqlite.Connection = Depends(get_db)):
    await db.execute("DELETE FROM skill_categories WHERE id = ?", (id,))
    await db.commit()
    return Response(status_code=204)


@router.post("/", status_code=201)
async def create_skill(request: Request, db: aiosqlite.Connection = Depends(get_db)):
    if request.headers.get("content-type", "").startswith("application/json"):
        data = await request.json()
    else:
        form = await request.form()
        data = dict(form)

    name = data.get("name", "").strip()
    category_id = data.get("category_id")
    if category_id == "" or category_id is None:
        category_id = None
    else:
        category_id = int(category_id)

    confidence = data.get("confidence", "proficient")
    evidence = data.get("evidence", "")

    await db.execute(
        """INSERT INTO skills (name, category_id, confidence, evidence, validated)
           VALUES (?, ?, ?, ?, 0)""",
        (name, category_id, confidence, evidence),
    )
    await db.commit()

    async with db.execute("SELECT * FROM skills WHERE id = last_insert_rowid()") as c:
        row = await c.fetchone()
    skill_dict = dict(row) if row else {}

    if request.headers.get("hx-request"):
        questions = await skill_validator.generate_single_test(name)
        return render_template(
            request=request,
            name="partials/test_modal.html",
            context={
                "skill": skill_dict,
                "questions": questions,
            },
        )

    return skill_dict


@router.delete("/{id}", status_code=204)
async def delete_skill(id: int, db: aiosqlite.Connection = Depends(get_db)):
    await db.execute("DELETE FROM skills WHERE id = ?", (id,))
    await db.commit()
    return Response(status_code=204)


@router.post("/bulk", status_code=201)
async def bulk_create_skills(request: Request, db: aiosqlite.Connection = Depends(get_db)):
    if request.headers.get("content-type", "").startswith("application/json"):
        data = await request.json()
    else:
        form = await request.form()
        data = dict(form)

    raw_names = data.get("names", "")
    if isinstance(raw_names, str):
        names = [n.strip() for n in raw_names.split(",") if n.strip()]
    else:
        names = raw_names

    category_id = data.get("category_id")
    if category_id:
        category_id = int(category_id)
    else:
        category_id = None

    confidence = data.get("confidence", "proficient")
    created = []
    for name in names:
        await db.execute(
            """INSERT INTO skills (name, confidence, category_id, validated)
               VALUES (?, ?, ?, 0)""",
            (name, confidence, category_id),
        )
        await db.commit()
        async with db.execute("SELECT * FROM skills WHERE id = last_insert_rowid()") as c:
            row = await c.fetchone()
        if row:
            created.append(dict(row))

    if request.headers.get("hx-request"):
        return HTMLResponse(
            f"""<div class="bg-indigo-50 border border-indigo-200 text-indigo-900 text-xs p-3 rounded-md mb-4 flex items-center justify-between">
                <span>Added {len(created)} skills in bulk as self-reported.</span>
                <a href="/skills" class="underline font-semibold ml-2">Refresh View</a>
            </div>"""
        )

    return created


@router.get("/{id}/test")
async def get_skill_test(id: int, request: Request, db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute("SELECT * FROM skills WHERE id = ?", (id,)) as c:
        skill = await c.fetchone()
    if not skill:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Skill not found")
    skill_dict = dict(skill)
    questions = await skill_validator.generate_single_test(skill_dict["name"])

    if "text/html" in request.headers.get("accept", "") or request.headers.get("hx-request"):
        return render_template(
            request=request,
            name="partials/test_modal.html",
            context={
                "skill": skill_dict,
                "questions": questions,
            },
        )

    return {
        "skill_id": id,
        "skill_name": skill_dict["name"],
        "questions": questions,
    }


@router.post("/{id}/test/submit")
async def submit_skill_test(id: int, request: Request, db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute("SELECT * FROM skills WHERE id = ?", (id,)) as c:
        skill = await c.fetchone()
    if not skill:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Skill not found")

    skill_dict = dict(skill)

    if request.headers.get("content-type", "").startswith("application/json"):
        data = await request.json()
        raw_answers = data.get("answers", [])
    else:
        form = await request.form()
        raw_answers = form.getlist("answers")

    result = await skill_validator.grade_and_store(id, skill_dict["name"], raw_answers, db)

    if "text/html" in request.headers.get("accept", "") or request.headers.get("hx-request"):
        return render_template(
            request=request,
            name="partials/test_result.html",
            context={
                "skill": skill_dict,
                "result": result,
            },
        )

    return result
