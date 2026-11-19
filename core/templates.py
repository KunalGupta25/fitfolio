from pathlib import Path
from fastapi import Request
from fastapi.responses import HTMLResponse
from starlette.templating import Jinja2Templates

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def render_template(
    request: Request,
    name: str,
    context: dict | None = None,
    status_code: int = 200,
) -> HTMLResponse:
    ctx = dict(context or {})
    return templates.TemplateResponse(
        request=request,
        name=name,
        context=ctx,
        status_code=status_code,
    )
