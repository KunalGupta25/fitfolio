from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import HTMLResponse
import aiosqlite
from core.database import get_db
from core.templates import render_template

router = APIRouter(prefix="/education")


@router.get("/")
@router.get("", include_in_schema=False)
async def list_education(request: Request, db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute(
        "SELECT * FROM education ORDER BY display_order ASC, id ASC"
    ) as c:
        rows = await c.fetchall()
    result = [dict(r) for r in rows]

    if "text/html" in request.headers.get("accept", ""):
        return render_template(
            request=request,
            name="education.html",
            context={"education": result},
        )

    return result


@router.post("/", status_code=201)
async def create_education(request: Request, db: aiosqlite.Connection = Depends(get_db)):
    if request.headers.get("content-type", "").startswith("application/json"):
        data = await request.json()
    else:
        form = await request.form()
        data = dict(form)

    institution = data.get("institution", "").strip()
    degree = data.get("degree", "").strip()
    specialization = data.get("specialization")
    cgpa = data.get("cgpa")
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    location = data.get("location")

    await db.execute(
        """INSERT INTO education (institution, degree, specialization, cgpa, start_date, end_date, location)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (institution, degree, specialization, cgpa, start_date, end_date, location),
    )
    await db.commit()

    async with db.execute("SELECT * FROM education WHERE id = last_insert_rowid()") as c:
        row = await c.fetchone()
    edu = dict(row) if row else {}

    if request.headers.get("hx-request"):
        spec_text = f" in {edu['specialization']}" if edu.get("specialization") else ""
        cgpa_text = f" · <span class='font-semibold text-slate-700'>CGPA: {edu['cgpa']}</span>" if edu.get("cgpa") else ""
        loc_text = f" · {edu['location']}" if edu.get("location") else ""
        return HTMLResponse(
            f"""<div id="edu-{edu.get('id')}" class="bg-white border border-slate-200 rounded-lg p-5 shadow-sm flex items-start justify-between">
              <div class="space-y-1">
                <h3 class="text-sm font-bold text-slate-800">{edu.get('institution')}</h3>
                <p class="text-xs text-slate-600">{edu.get('degree')}{spec_text}{cgpa_text}</p>
                <p class="text-xs text-slate-400">{edu.get('start_date', '')} -- {edu.get('end_date', '')}{loc_text}</p>
              </div>
              <button
                hx-delete="/education/{edu.get('id')}"
                hx-target="#edu-{edu.get('id')}"
                hx-swap="outerHTML"
                class="text-slate-400 hover:text-red-500 text-xs px-2 py-1 rounded"
              >✕ Delete</button>
            </div>"""
        )

    return edu


@router.delete("/{id}", status_code=204)
async def delete_education(id: int, db: aiosqlite.Connection = Depends(get_db)):
    await db.execute("DELETE FROM education WHERE id = ?", (id,))
    await db.commit()
    return Response(status_code=204)
