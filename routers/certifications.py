from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import HTMLResponse
import aiosqlite
from core.database import get_db
from core.templates import render_template

router = APIRouter(prefix="/certifications")


@router.get("/")
@router.get("", include_in_schema=False)
async def list_certifications(request: Request, db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute(
        "SELECT * FROM certifications ORDER BY display_order ASC, id ASC"
    ) as c:
        rows = await c.fetchall()
    result = [dict(r) for r in rows]

    if "text/html" in request.headers.get("accept", ""):
        return render_template(
            request=request,
            name="certifications.html",
            context={"certifications": result},
        )

    return result


@router.post("/", status_code=201)
async def create_certification(request: Request, db: aiosqlite.Connection = Depends(get_db)):
    if request.headers.get("content-type", "").startswith("application/json"):
        data = await request.json()
    else:
        form = await request.form()
        data = dict(form)

    name = data.get("name", "").strip()
    issuer = data.get("issuer", "").strip()
    issued_date = data.get("issued_date")
    url = data.get("url")

    await db.execute(
        "INSERT INTO certifications (name, issuer, issued_date, url) VALUES (?, ?, ?, ?)",
        (name, issuer, issued_date, url),
    )
    await db.commit()

    async with db.execute("SELECT * FROM certifications WHERE id = last_insert_rowid()") as c:
        row = await c.fetchone()
    cert = dict(row) if row else {}

    if request.headers.get("hx-request"):
        url_link = f"<a href='{cert['url']}' target='_blank' class='text-indigo-600 font-normal text-xs ml-1 hover:underline'>↗</a>" if cert.get("url") else ""
        date_text = f" · {cert['issued_date']}" if cert.get("issued_date") else ""
        return HTMLResponse(
            f"""<div id="cert-{cert.get('id')}" class="bg-white border border-slate-200 rounded-lg p-4 shadow-sm flex items-center justify-between">
              <div>
                <h3 class="text-sm font-bold text-slate-800">{cert.get('name')}{url_link}</h3>
                <p class="text-xs text-slate-500 mt-0.5">{cert.get('issuer')}{date_text}</p>
              </div>
              <button
                hx-delete="/certifications/{cert.get('id')}"
                hx-target="#cert-{cert.get('id')}"
                hx-swap="outerHTML"
                class="text-slate-400 hover:text-red-500 text-xs px-2 py-1 rounded"
              >✕ Delete</button>
            </div>"""
        )

    return cert


@router.delete("/{id}", status_code=204)
async def delete_certification(id: int, db: aiosqlite.Connection = Depends(get_db)):
    await db.execute("DELETE FROM certifications WHERE id = ?", (id,))
    await db.commit()
    return Response(status_code=204)
