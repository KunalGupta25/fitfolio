import aiosqlite

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS personal_info (
    id INTEGER PRIMARY KEY DEFAULT 1,
    full_name TEXT NOT NULL DEFAULT '',
    phone TEXT DEFAULT '',
    email TEXT NOT NULL DEFAULT '',
    linkedin TEXT DEFAULT '',
    github TEXT DEFAULT '',
    portfolio TEXT DEFAULT '',
    city TEXT DEFAULT '',
    state TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS summary (
    id INTEGER PRIMARY KEY DEFAULT 1,
    raw_bio TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS education (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    institution TEXT NOT NULL,
    degree TEXT NOT NULL,
    specialization TEXT,
    cgpa TEXT,
    start_date TEXT,
    end_date TEXT,
    location TEXT,
    display_order INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS skill_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    display_order INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER REFERENCES skill_categories(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    confidence TEXT CHECK(confidence IN ('expert','proficient','familiar')) DEFAULT 'proficient',
    validated INTEGER DEFAULT 0,
    test_score REAL,
    evidence TEXT
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    tag TEXT,
    live_url TEXT,
    github_url TEXT,
    start_date TEXT,
    end_date TEXT,
    display_order INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS project_bullets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    bullet TEXT NOT NULL,
    keywords TEXT,
    display_order INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS experience (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    organization TEXT NOT NULL,
    location TEXT,
    start_date TEXT,
    end_date TEXT,
    display_order INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS experience_bullets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    experience_id INTEGER NOT NULL REFERENCES experience(id) ON DELETE CASCADE,
    bullet TEXT NOT NULL,
    keywords TEXT,
    display_order INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS certifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    issuer TEXT NOT NULL,
    issued_date TEXT,
    url TEXT,
    display_order INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS resume_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    jd_text TEXT,
    jd_role TEXT,
    jd_company TEXT,
    output_path TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

from core.config import settings


async def init_db() -> None:
    async with aiosqlite.connect(settings.database_url) as db:
        await db.executescript(CREATE_TABLES_SQL)
        await db.commit()


async def get_db():
    async with aiosqlite.connect(settings.database_url) as db:
        db.row_factory = aiosqlite.Row
        yield db
