from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import HTMLResponse
import aiosqlite
from core.database import get_db
from core.templates import render_template

router = APIRouter(prefix="/experience")


async def _get_exp_with_bullets(db: aiosqlite.Connection, exp_id: int):
    async with db.execute("SELECT * FROM experience WHERE id = ?", (exp_id,)) as c:
        row = await c.fetchone()
    if not row:
        return None
    d = dict(row)
    async with db.execute(
        "SELECT * FROM experience_bullets WHERE experience_id = ? ORDER BY display_order ASC, id ASC",
        (exp_id,),
    ) as c:
        bullets = await c.fetchall()
    d["bullets"] = [dict(b) for b in bullets]
    return d


@router.get("/")
@router.get("", include_in_schema=False)
async def list_experience(request: Request, db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute(
        "SELECT * FROM experience ORDER BY display_order ASC, id ASC"
    ) as c:
        rows = await c.fetchall()
    result = []
    for r in rows:
        d = dict(r)
        async with db.execute(
            "SELECT * FROM experience_bullets WHERE experience_id = ? ORDER BY display_order ASC, id ASC",
            (d["id"],),
        ) as bc:
            bullets = await bc.fetchall()
        d["bullets"] = [dict(b) for b in bullets]
        result.append(d)

    if "text/html" in request.headers.get("accept", ""):
        return render_template(
            request=request,
            name="experience.html",
            context={"experience": result},
        )

    return result


@router.post("/", status_code=201)
async def create_experience(request: Request, db: aiosqlite.Connection = Depends(get_db)):
    if request.headers.get("content-type", "").startswith("application/json"):
        data = await request.json()
    else:
        form = await request.form()
        data = dict(form)

    role = data.get("role", "").strip()
    organization = data.get("organization", "").strip()
    location = data.get("location", "")
    start_date = data.get("start_date", "")
    end_date = data.get("end_date", "")

    await db.execute(
        """INSERT INTO experience (role, organization, location, start_date, end_date)
           VALUES (?, ?, ?, ?, ?)""",
        (role, organization, location, start_date, end_date),
    )
    await db.commit()

    async with db.execute("SELECT last_insert_rowid() as lid") as c:
        exp_id = (await c.fetchone())["lid"]

    exp = await _get_exp_with_bullets(db, exp_id)

    if request.headers.get("hx-request"):
        return HTMLResponse(
            f"""<div id="experience-{exp['id']}" class="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-4">
              <div class="flex items-start justify-between">
                <div>
                  <h3 class="text-sm font-bold text-slate-800">{exp['role']}</h3>
                  <p class="text-xs text-slate-600 font-medium">{exp['organization']} · {exp.get('location', '')}</p>
                  <p class="text-xs text-slate-400 mt-0.5">{exp.get('start_date', '')} -- {exp.get('end_date', '')}</p>
                </div>
                <button
                  hx-delete="/experience/{exp['id']}"
                  hx-target="#experience-{exp['id']}"
                  hx-swap="outerHTML"
                  class="text-slate-400 hover:text-red-500 text-xs px-2 py-1 rounded"
                >✕ Delete</button>
              </div>
            </div>"""
        )

    return exp


@router.delete("/{id}", status_code=204)
async def delete_experience(id: int, db: aiosqlite.Connection = Depends(get_db)):
    await db.execute("DELETE FROM experience WHERE id = ?", (id,))
    await db.commit()
    return Response(status_code=204)


@router.post("/{id}/bullets", status_code=201)
async def add_bullet(id: int, request: Request, db: aiosqlite.Connection = Depends(get_db)):
    if request.headers.get("content-type", "").startswith("application/json"):
        data = await request.json()
    else:
        form = await request.form()
        data = dict(form)

    bullet_text = data.get("bullet", "").strip()
    keywords = data.get("keywords", "").strip()

    await db.execute(
        """INSERT INTO experience_bullets (experience_id, bullet, keywords, display_order)
           VALUES (?, ?, ?, 0)""",
        (id, bullet_text, keywords),
    )
    await db.commit()

    async with db.execute("SELECT * FROM experience_bullets WHERE id = last_insert_rowid()") as c:
        b_row = await c.fetchone()
    b_dict = dict(b_row) if b_row else {}

    if request.headers.get("hx-request"):
        return HTMLResponse(
            f"""<li id="exp-bullet-{b_dict.get('id')}" class="flex items-start justify-between gap-3 text-xs text-slate-700 bg-slate-50 px-3 py-2 rounded border border-slate-100 group">
              <span class="flex-1">• {b_dict.get('bullet')}</span>
              <button
                hx-delete="/experience/bullets/{b_dict.get('id')}"
                hx-target="#exp-bullet-{b_dict.get('id')}"
                hx-swap="outerHTML"
                class="text-slate-300 hover:text-red-500 transition-colors text-xs opacity-0 group-hover:opacity-100 px-1"
              >✕</button>
            </li>"""
        )

    return b_dict


@router.delete("/bullets/{bullet_id}", status_code=204)
async def delete_bullet(bullet_id: int, db: aiosqlite.Connection = Depends(get_db)):
    await db.execute("DELETE FROM experience_bullets WHERE id = ?", (bullet_id,))
    await db.commit()
    return Response(status_code=204)
