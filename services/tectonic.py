import asyncio
import os
import shutil
import subprocess
import uuid
from pathlib import Path
from core.config import settings


async def compile_latex(
    tex_content: str, session_id: str | int | None = None
) -> tuple[str, str]:
    """Compiles LaTeX string using Tectonic binary.

    Returns:
        tuple: (session_id_str, pdf_output_path)
    """
    if session_id is None:
        session_id_str = uuid.uuid4().hex[:8]
    else:
        session_id_str = str(session_id)

    out_dir = Path(settings.output_dir) / session_id_str
    out_dir.mkdir(parents=True, exist_ok=True)

    tex_file = out_dir / "resume.tex"
    tex_file.write_text(tex_content, encoding="utf-8")

    pdf_file = out_dir / "resume.pdf"

    # Check if tectonic binary is found
    tectonic_bin = shutil.which(settings.tectonic_path) or settings.tectonic_path

    try:
        proc = await asyncio.to_thread(
            subprocess.run,
            [tectonic_bin, "--outdir", str(out_dir), str(tex_file)],
            capture_output=True,
            text=True,
            cwd=str(out_dir),
        )

        if proc.returncode != 0:
            # If tectonic fails, write error log
            (out_dir / "error.log").write_text(proc.stderr, encoding="utf-8")
            raise RuntimeError(f"Tectonic compilation failed:\n{proc.stderr}")

    except (FileNotFoundError, OSError) as e:
        # If tectonic is not installed on this machine, save mock/placeholder PDF or raise
        raise RuntimeError(
            f"Tectonic binary not found at '{settings.tectonic_path}'. "
            f"Please install Tectonic or ensure it is on PATH. LaTeX source saved at {tex_file}."
        ) from e

    return session_id_str, str(pdf_file)
