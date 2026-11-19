from fastapi import APIRouter, Depends, Request, Response
import aiosqlite
from core.database import get_db
from core.templates import render_template

router = APIRouter(prefix="/projects")


async def _get_project_with_bullets(db: aiosqlite.Connection, project_id: int):
    async with db.execute("SELECT * FROM projects WHERE id = ?", (project_id,)) as c:
        project = await c.fetchone()
    if not project:
        return None
    project_dict = dict(project)
    async with db.execute(
        "SELECT * FROM project_bullets WHERE project_id = ? ORDER BY display_order ASC, id ASC",
        (project_id,),
    ) as c:
        bullets = await c.fetchall()
    project_dict["bullets"] = [dict(b) for b in bullets]
    return project_dict


@router.get("/")
@router.get("", include_in_schema=False)
async def list_projects(request: Request, db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute(
        "SELECT * FROM projects ORDER BY display_order ASC, id ASC"
    ) as c:
        projects = await c.fetchall()
    result = []
    for p in projects:
        async with db.execute(
            "SELECT * FROM project_bullets WHERE project_id = ? ORDER BY display_order ASC, id ASC",
            (p["id"],),
        ) as bc:
            bullets = await bc.fetchall()
        pd = dict(p)
        pd["bullets"] = [dict(b) for b in bullets]
        result.append(pd)

    if "text/html" in request.headers.get("accept", ""):
        return render_template(
            request=request,
            name="projects.html",
            context={"projects": result},
        )

    return result


@router.post("/", status_code=201)
async def create_project(request: Request, db: aiosqlite.Connection = Depends(get_db)):
    if request.headers.get("content-type", "").startswith("application/json"):
        data = await request.json()
    else:
        form = await request.form()
        data = dict(form)

    await db.execute(
        """INSERT INTO projects (name, tag, live_url, github_url, start_date, end_date, display_order, is_active)
           VALUES (:name, :tag, :live_url, :github_url, :start_date, :end_date, :display_order, :is_active)""",
        {
            "name": data.get("name", "").strip(),
            "tag": data.get("tag"),
            "live_url": data.get("live_url"),
            "github_url": data.get("github_url"),
            "start_date": data.get("start_date"),
            "end_date": data.get("end_date"),
            "display_order": int(data.get("display_order", 0)),
            "is_active": 1,
        },
    )
    await db.commit()
    async with db.execute("SELECT last_insert_rowid() as lid") as c:
        row = await c.fetchone()
        project_id = row["lid"]

    project = await _get_project_with_bullets(db, project_id)

    if request.headers.get("hx-request"):
        return render_template(
            request=request,
            name="partials/project_card.html",
            context={"project": project},
        )

    return project


@router.delete("/{id}", status_code=204)
async def delete_project(id: int, db: aiosqlite.Connection = Depends(get_db)):
    await db.execute("DELETE FROM projects WHERE id = ?", (id,))
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
        """INSERT INTO project_bullets (project_id, bullet, keywords, display_order)
           VALUES (?, ?, ?, 0)""",
        (id, bullet_text, keywords),
    )
    await db.commit()

    async with db.execute("SELECT * FROM project_bullets WHERE id = last_insert_rowid()") as c:
        b_row = await c.fetchone()
    b_dict = dict(b_row) if b_row else {}

    if request.headers.get("hx-request"):
        return render_template(
            request=request,
            name="partials/bullet_row.html",
            context={"bullet": b_dict},
        )

    return b_dict


@router.delete("/bullets/{bullet_id}", status_code=204)
async def delete_bullet(bullet_id: int, db: aiosqlite.Connection = Depends(get_db)):
    await db.execute("DELETE FROM project_bullets WHERE id = ?", (bullet_id,))
    await db.commit()
    return Response(status_code=204)
