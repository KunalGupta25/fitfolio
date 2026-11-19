# fitFolio

> **A personal, skill-validated resume engine with zero assumptions.**  
> Stores your verified technical profile, tests your skills, and drafts ATS-optimized resumes tailored to any Job Description.

---

## 🚀 Key Features

- **No AI Hallucinations / Assumed Skills**: Only incorporates technologies, projects, and experiences you have explicitly documented in your database.
- **Skill Validation Engine**: Generates concise technical tests to validate skills (single or bulk), tagging them as `Validated ✅` or `Self-Reported ○`.
- **Targeted Resume Generation**: Takes any job description, extracts must-have skills and ATS keywords, scores your profile against it, and generates section-wise LaTeX resumes.
- **ATS-Optimized Output**: Single-column, clean layout using standard LaTeX and Tectonic for PDF compilation.
- **Dual Transport Integration**:
  - **FastMCP Server**: Exposes 10 native tools, prompts, and resources over HTTP for Claude Desktop, Claude Web, Cursor, and Windsurf.
  - **OpenAPI REST API**: Native `/openapi.json` for ChatGPT GPT Actions and web clients.
- **Lightweight Architecture**: Single Python process, SQLite storage, and interactive web UI via Jinja2 + HTMX + Alpine.js (zero Node.js dependencies).

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | FastAPI (Python 3.12+) |
| **Database** | SQLite via `aiosqlite` |
| **MCP Server** | FastMCP (over Streamable HTTP) |
| **Frontend** | Jinja2 + HTMX + Alpine.js + TailwindCSS |
| **AI Evaluation** | Google Gemini API (`gemini-2.0-flash`) |
| **PDF Compilation** | Tectonic LaTeX Engine |

---

## 📂 Project Structure

```
fitfolio/
├── main.py                        # FastAPI web application entry point
├── mcp_server.py                  # FastMCP server entry point (port 8001)
├── requirements.txt
├── .env.example
├── Dockerfile
├── core/
│   ├── config.py                  # Environment settings & configuration
│   ├── database.py                # Async SQLite connection & schema initialization
│   ├── models.py                  # Pydantic models for all entities
│   └── templates.py               # Jinja2 template rendering helper
├── routers/
│   ├── profile.py                 # /profile (personal info, bio, completeness)
│   ├── skills.py                  # /skills (skills, categories, validation tests)
│   ├── projects.py                # /projects (projects & achievement bullets)
│   ├── experience.py              # /experience (work history & bullets)
│   ├── education.py               # /education (degrees, dates, GPA)
│   ├── certifications.py          # /certifications (credentials)
│   └── resume.py                  # /resume (JD analysis, LaTeX builder, PDF export)
├── services/
│   ├── gemini.py                  # Unified Gemini API integration
│   ├── jd_analyzer.py             # Extracts must-haves, nice-to-haves & keywords
│   ├── skill_validator.py         # Test generation & answer grading
│   ├── resume_builder.py          # Section-by-section LaTeX population
│   └── tectonic.py                # Tectonic PDF compilation pipeline
├── mcp_tools/
│   └── tools.py                   # 10 MCP tools, prompts & resources
├── templates/                     # Jinja2 HTML views
│   ├── base.html                  # Sidebar layout & CDN dependencies
│   ├── dashboard.html             # Profile completeness dashboard
│   ├── profile.html               # Personal info & bio editor
│   ├── skills.html                # Skills & category management
│   ├── projects.html              # Projects manager
│   ├── experience.html            # Experience manager
│   ├── education.html             # Education manager
│   ├── certifications.html        # Certifications manager
│   ├── resume.html                # Targeted generator UI
│   └── partials/                  # Dynamic HTMX components
└── latex/
    └── template.tex               # ATS-safe LaTeX resume template with placeholders
```

---

## ⚡ Quick Start

### 1. Clone & Configure
```bash
git clone https://github.com/KunalGupta25/fitfolio.git
cd fitfolio
cp .env.example .env
```
Edit `.env` and set your `GEMINI_API_KEY`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

*(Optional for local PDF compilation)* Install Tectonic:
- **macOS / Linux**: `curl --proto '=https' --tlsv1.2 -fsSL https://drop.science/tectonic/install.sh | sh`
- **Windows**: Download `tectonic.exe` from [Tectonic releases](https://tectonic-typesetting.github.io) and add to PATH.

### 3. Run the Web App
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Open your browser at [http://localhost:8000](http://localhost:8000).

---

## 🤖 MCP Server Setup (Claude Desktop, Cursor, etc.)

Start the MCP server:
```bash
python mcp_server.py
```
By default, the server runs on `http://localhost:8001/mcp`.

### Configure Claude Desktop (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "fitfolio": {
      "url": "http://localhost:8001/mcp"
    }
  }
}
```

### Available MCP Tools:
1. `get_full_profile()`: Returns complete profile data across all sections.
2. `get_skills(validated_only)`: Returns skills with validation status and confidence.
3. `get_projects(limit)`: Returns active projects with achievement bullets.
4. `analyze_jd(jd_text)`: Extracts requirements, preferred skills, and ATS keywords from a job posting.
5. `get_relevant_sections(jd_text)`: Scores projects and skills against a JD.
6. `start_validation_test(skill_name)`: Generates a 3-4 question technical assessment.
7. `submit_validation_answers(skill_name, answers)`: Evaluates answers and updates skill verification status in SQLite.
8. `start_bulk_validation_test(skill_names)`: Identifies hardest skills and generates a combined test.
9. `generate_resume_latex(jd_text, max_pages)`: Compiles an honest, tailored LaTeX resume section-by-section.
10. `log_resume_session(jd_role, jd_company, jd_text, output_path)`: Logs the generated session.

---

## 🌐 ChatGPT GPT Actions

Because fitFolio is built on FastAPI, the OpenAPI specification is available at `http://localhost:8000/openapi.json`.
1. Go to ChatGPT → **Explore GPTs** → **Create a GPT** → **Configure**.
2. Click **Add Action** → **Import from URL** and paste your `openapi.json` URL.
3. ChatGPT can now inspect and draft resumes directly using your verified profile endpoints.

---

## 🐳 Docker Deployment

```bash
docker build -t fitfolio .
docker run -p 8000:8000 -p 8001:8001 -e GEMINI_API_KEY="your_key" fitfolio
```

---

## 📄 License
MIT License. Built for developers and students seeking honest, tailored career acceleration.
