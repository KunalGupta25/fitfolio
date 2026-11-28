import asyncio
import aiosqlite
from core.database import init_db

async def seed():
    await init_db()
    async with aiosqlite.connect("./fitfolio.db") as db:
        # 1. Personal Info
        await db.execute(
            """INSERT OR REPLACE INTO personal_info 
               (id, full_name, phone, email, linkedin, github, portfolio, city, state)
               VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "Kunal Gupta",
                "+91 9999999999",
                "kunalgupta@gmail.com",
                "Kunalgupta25",
                "KunalGupta25",
                "https://kunalgupta.mexus.tech/",
                "Jodhpur",
                "Rajasthan",
            ),
        )

        # 2. Summary
        raw_bio = (
            "AI Developer and CS Engineering student (AI specialization, 2027) with hands-on "
            "experience building RAG systems, vector database pipelines, and locally-deployed LLM applications. "
            "Shipped production AI systems using LangChain, LlamaIndex, ChromaDB, FAISS, and Ollama -- from "
            "document ingestion pipeline design (PDFs, web content) to local server deployment. Experienced "
            "setting up and integrating local LLMs (LLaMA, Mistral, GPT4All via Ollama) with vector stores for "
            "context-aware retrieval; focused on building reliable inference pipelines with close attention to "
            "latency, memory efficiency, and embedding quality."
        )
        await db.execute("INSERT OR REPLACE INTO summary (id, raw_bio) VALUES (1, ?)", (raw_bio,))

        # 3. Education
        await db.execute("DELETE FROM education")
        await db.execute(
            """INSERT INTO education (institution, degree, specialization, cgpa, start_date, end_date, location, display_order)
               VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
            (
                "Parul University",
                "B.Tech",
                "Computer Science (AI)",
                "7.57",
                "Aug. 2023",
                "May 2027 (Expected)",
                "Vadodara, Gujarat",
            ),
        )

        # 4. Skill Categories & Skills
        await db.execute("DELETE FROM skills")
        await db.execute("DELETE FROM skill_categories")

        categories_data = [
            ("LLM & Agent Frameworks", 1, [
                "LangChain", "LlamaIndex", "Smolagents", "LangGraph", "Hugging Face Transformers", "llama.cpp"
            ]),
            ("RAG & Vector DBs", 2, [
                "ChromaDB", "FAISS", "Semantic Chunking", "Embedding Pipelines", "Retrieval Reranking"
            ]),
            ("Local LLM Deployment", 3, [
                "Ollama", "LLaMA", "Mistral", "Qwen", "Latency & Memory Profiling"
            ]),
            ("Languages & Backend", 4, [
                "Python", "JavaScript", "TypeScript", "Java", "FastAPI", "Flask", "Django", "Node.js", "Express.js", "REST APIs"
            ]),
            ("Databases & Infrastructure", 5, [
                "MongoDB", "MySQL", "Firebase", "SQLite", "Docker", "AWS", "Vercel", "Cloudflare Workers", "Git"
            ]),
            ("Frontend", 6, [
                "React", "Next.js", "Streamlit", "Tailwind CSS", "Gradio"
            ]),
        ]

        for cat_name, order, skill_list in categories_data:
            await db.execute(
                "INSERT INTO skill_categories (name, display_order) VALUES (?, ?)",
                (cat_name, order),
            )
            async with db.execute("SELECT last_insert_rowid() as lid") as c:
                cat_id = (await c.fetchone())[0]

            for s_name in skill_list:
                # Mark core framework skills as validated=1 for initial seeding
                is_validated = 1 if s_name in ["LangChain", "FastAPI", "Python", "ChromaDB", "Docker", "React"] else 0
                await db.execute(
                    """INSERT INTO skills (category_id, name, confidence, validated, test_score, evidence)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (cat_id, s_name, "expert" if is_validated else "proficient", is_validated, 90.0 if is_validated else None, "Used in production and personal projects"),
                )

        # 5. Projects & Bullets
        await db.execute("DELETE FROM project_bullets")
        await db.execute("DELETE FROM projects")

        projects_data = [
            (
                "NoteRootAI",
                "Agentic LLM-Powered Knowledge System",
                "https://noteroot-ai.vercel.app/",
                "",
                "Jan. 2025",
                "Present",
                1,
                [
                    ("Architected a multi-provider LLM backend (FastAPI + Python) supporting OpenAI-compatible endpoints (Gemini, Groq, etc.) via a unified BYOK factory -- enabling one-line switching between cloud and locally-served models (LLaMA, Mistral)", "FastAPI,Python,LLM,LLaMA"),
                    ("Built an autonomous AI agent with tool-use (CRUD on notes, graph traversal via Neo4j) and a RAG pipeline (ChromaDB, semantic chunking, cosine similarity-based embedding search) for contextual note retrieval across a personal knowledge graph", "RAG,ChromaDB,Neo4j,Embeddings"),
                ]
            ),
            (
                "Plexi",
                "Production RAG Study Assistant",
                "https://plexi.mexus.tech/",
                "",
                "Jan. 2024",
                "Present",
                2,
                [
                    ("Designed an end-to-end document ingestion and RAG pipeline with LlamaIndex and LangChain -- covering PDF/text ingestion, chunking strategy, embedding generation, vector storage in ChromaDB, and query-time retrieval across 200+ documents", "LlamaIndex,LangChain,ChromaDB,RAG"),
                    ("Implemented multi-agent orchestration with Smolagents, splitting query decomposition, vector store retrieval, and response synthesis across independent agents for domain-specific academic content", "Smolagents,Multi-Agent,Agents"),
                    ("Evolved from Streamlit monolith (V1) to production microservices (V2: FastAPI retrieval API + Next.js on Cloudflare Workers); exposed RAG capabilities as queryable REST endpoints consumable by any client or UI", "FastAPI,Next.js,Cloudflare Workers,REST"),
                ]
            ),
            (
                "Chat-with-PDF",
                "Conversational Document QA System",
                "",
                "https://github.com/KunalGupta25/chat-with-pdf/",
                "Nov. 2023",
                "Jan. 2024",
                3,
                [
                    ("Built a document ingestion and conversational RAG pipeline enabling natural language Q&A over user-uploaded PDFs using LangChain, FAISS vector store, and Gemini API as the LLM backbone", "LangChain,FAISS,Gemini,PDF"),
                    ("Deployed as a Streamlit web app with session-level isolated vector indices per user -- preventing cross-session data leakage across concurrent users", "Streamlit,Vector DB,Isolation"),
                ]
            ),
        ]

        for p_name, tag, live_url, gh_url, s_date, e_date, p_order, bullets in projects_data:
            await db.execute(
                """INSERT INTO projects (name, tag, live_url, github_url, start_date, end_date, display_order, is_active)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
                (p_name, tag, live_url, gh_url, s_date, e_date, p_order),
            )
            async with db.execute("SELECT last_insert_rowid() as lid") as c:
                proj_id = (await c.fetchone())[0]

            for b_idx, (b_text, b_kws) in enumerate(bullets):
                await db.execute(
                    """INSERT INTO project_bullets (project_id, bullet, keywords, display_order)
                       VALUES (?, ?, ?, ?)""",
                    (proj_id, b_text, b_kws, b_idx + 1),
                )

        # 6. Experience & Bullets
        await db.execute("DELETE FROM experience_bullets")
        await db.execute("DELETE FROM experience")

        await db.execute(
            """INSERT INTO experience (role, organization, location, start_date, end_date, display_order)
               VALUES (?, ?, ?, ?, ?, 1)""",
            (
                "Coordinator, Career Development Cell",
                "Parul Institute of Technology",
                "Vadodara",
                "July 2024",
                "February 2025",
            ),
        )
        async with db.execute("SELECT last_insert_rowid() as lid") as c:
            exp_id = (await c.fetchone())[0]

        exp_bullets = [
            ("Contributed to technical and content teams for Fun Fest 2024, Gujarat's largest non-technical event with 2,000+ participants across 15+ competitions", "Events,Coordination"),
            ("Managed event registration and data workflow using Google Sheets and Excel, processing 2,000+ records with zero data loss", "Data Workflow,Excel"),
            ("Led technical team for Mic Master 2025, Parul University's largest speaking event with 500+ participants", "Leadership,Technical"),
        ]
        for b_idx, (b_text, b_kws) in enumerate(exp_bullets):
            await db.execute(
                """INSERT INTO experience_bullets (experience_id, bullet, keywords, display_order)
                   VALUES (?, ?, ?, ?)""",
                (exp_id, b_text, b_kws, b_idx + 1),
            )

        # 7. Certifications
        await db.execute("DELETE FROM certifications")
        certs_data = [
            ("Building RAG Agents with LLMs", "NVIDIA", "Sep. 2025", ""),
            ("Fundamentals of Agents", "Hugging Face", "May 2025", ""),
            ("AI Infrastructure & Ops Fundamentals", "Coursera", "Jan. 2025", ""),
            ("AWS Cloud Practitioner Essentials", "Coursera", "Aug. 2025", ""),
            ("Software Engineering Virtual Experience", "Skyscanner/Forage", "May 2025", ""),
            ("Computer Networks and Internet Protocol", "NPTEL", "May 2025", ""),
        ]
        for c_idx, (c_name, issuer, i_date, url) in enumerate(certs_data):
            await db.execute(
                """INSERT INTO certifications (name, issuer, issued_date, url, display_order)
                   VALUES (?, ?, ?, ?, ?)""",
                (c_name, issuer, i_date, url, c_idx + 1),
            )

        await db.commit()
        print("Successfully seeded fitfolio.db with Kunal's complete profile data!")

if __name__ == "__main__":
    asyncio.run(seed())
