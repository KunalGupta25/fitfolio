import asyncio
import aiosqlite
from core.database import init_db

async def seed():
    await init_db()
    async with aiosqlite.connect("fitfolio.db") as db:
        # 1. Personal Info
        await db.execute("""
            INSERT OR REPLACE INTO personal_info 
            (id, full_name, phone, email, linkedin, github, portfolio, city, state)
            VALUES (
                1, 
                'Kunal Gupta', 
                '+91 99999999999', 
                'kunalgupta@gmail.com', 
                'Kunalgupta25', 
                'KunalGupta25', 
                'https://kunalgupta.mexus.tech', 
                'Jodhpur', 
                'Rajasthan'
            )
        """)

        # 2. Raw Bio / Summary
        await db.execute("""
            INSERT OR REPLACE INTO summary (id, raw_bio)
            VALUES (
                1, 
                'AI Developer and CS Engineering student (AI specialization, 2027) with hands-on experience building RAG systems, vector database pipelines, and locally-deployed LLM applications. Shipped production AI systems using LangChain, LlamaIndex, ChromaDB, FAISS, and Ollama from document ingestion pipeline design (PDFs, web content) to local server deployment. Experienced setting up and integrating local LLMs (LLaMA, Mistral, GPT4All via Ollama) with vector stores for context-aware retrieval; focused on building reliable inference pipelines with close attention to latency, memory efficiency, and embedding quality.'
            )
        """)

        # 3. Education
        await db.execute("DELETE FROM education")
        await db.execute("""
            INSERT INTO education (institution, degree, specialization, cgpa, start_date, end_date, location, display_order)
            VALUES (
                'Parul University',
                'B.Tech',
                'Computer Science (AI)',
                '7.57',
                'Aug. 2023',
                'May 2027 (Expected)',
                'Vadodara, Gujarat',
                1
            )
        """)

        # 4. Skill Categories & Skills
        await db.execute("DELETE FROM skills")
        await db.execute("DELETE FROM skill_categories")

        categories = [
            ("LLM & Agent Frameworks", [
                ("LangChain", "expert", 1, 95.0, "Built NoteRootAI & Chat-with-PDF"),
                ("LlamaIndex", "expert", 1, 92.0, "Production RAG in Plexi study assistant"),
                ("Smolagents", "proficient", 1, 88.0, "Multi-agent orchestration in Plexi"),
                ("LangGraph", "proficient", 0, None, None),
                ("Hugging Face Transformers", "proficient", 0, None, None),
                ("llama.cpp", "familiar", 0, None, None)
            ]),
            ("RAG & Vector DBs", [
                ("ChromaDB", "expert", 1, 95.0, "Vector store in NoteRootAI & Plexi"),
                ("FAISS", "expert", 1, 90.0, "Used in Chat-with-PDF session indices"),
                ("Semantic Chunking", "proficient", 1, 85.0, None),
                ("Embedding Pipelines", "expert", 1, 92.0, None),
                ("Retrieval Reranking", "proficient", 0, None, None)
            ]),
            ("Local LLM Deployment", [
                ("Ollama", "expert", 1, 95.0, "Served LLaMA & Mistral locally"),
                ("LLaMA", "proficient", 1, 88.0, None),
                ("Mistral", "proficient", 1, 88.0, None),
                ("Qwen", "proficient", 0, None, None),
                ("Latency & Memory Profiling", "proficient", 0, None, None)
            ]),
            ("Languages & Backend", [
                ("Python", "expert", 1, 95.0, "Primary language across all AI projects"),
                ("JavaScript", "proficient", 0, None, None),
                ("TypeScript", "proficient", 0, None, None),
                ("FastAPI", "expert", 1, 92.0, "Plexi V2 backend & NoteRootAI API"),
                ("Flask", "proficient", 0, None, None),
                ("REST APIs", "expert", 1, 94.0, None)
            ]),
            ("Databases & Infrastructure", [
                ("MongoDB", "proficient", 0, None, None),
                ("SQLite", "expert", 1, 90.0, "fitFolio database"),
                ("Docker", "proficient", 1, 85.0, None),
                ("Cloudflare Workers", "proficient", 0, None, None),
                ("Git", "expert", 1, 95.0, None)
            ]),
            ("Frontend", [
                ("React", "proficient", 0, None, None),
                ("Next.js", "proficient", 0, None, None),
                ("Streamlit", "expert", 1, 90.0, "Deployed Chat-with-PDF and Plexi V1"),
                ("Tailwind CSS", "proficient", 0, None, None)
            ])
        ]

        for cat_order, (cat_name, skill_list) in enumerate(categories, 1):
            await db.execute(
                "INSERT INTO skill_categories (name, display_order) VALUES (?, ?)",
                (cat_name, cat_order)
            )
            async with db.execute("SELECT last_insert_rowid() as lid") as c:
                cat_id = (await c.fetchone())[0]

            for s_name, conf, val, score, evid in skill_list:
                await db.execute("""
                    INSERT INTO skills (category_id, name, confidence, validated, test_score, evidence)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (cat_id, s_name, conf, val, score, evid))

        # 5. Projects & Bullets
        await db.execute("DELETE FROM project_bullets")
        await db.execute("DELETE FROM projects")

        # Project 1: NoteRootAI
        await db.execute("""
            INSERT INTO projects (name, tag, live_url, github_url, start_date, end_date, display_order, is_active)
            VALUES (
                'NoteRootAI', 
                'Agentic LLM-Powered Knowledge System', 
                'https://noteroot-ai.vercel.app/', 
                NULL, 
                'Jan. 2025', 
                'Present', 
                1, 
                1
            )
        """)
        async with db.execute("SELECT last_insert_rowid() as lid") as c:
            p1_id = (await c.fetchone())[0]

        await db.execute("""
            INSERT INTO project_bullets (project_id, bullet, keywords, display_order) VALUES 
            (?, 'Architected a multi-provider LLM backend (FastAPI + Python) supporting OpenAI-compatible endpoints (Gemini, Groq) via a unified BYOK factory, enabling one-line switching between cloud and locally-served models (LLaMA, Mistral).', 'FastAPI,Python,LLaMA,Mistral,Groq,Gemini', 1),
            (?, 'Built an autonomous AI agent with tool-use (CRUD on notes, graph traversal via Neo4j) and a RAG pipeline (ChromaDB, semantic chunking, cosine similarity-based embedding search) for contextual note retrieval across a personal knowledge graph.', 'AI Agent,Neo4j,ChromaDB,RAG,Semantic Chunking', 2)
        """, (p1_id, p1_id))

        # Project 2: Plexi
        await db.execute("""
            INSERT INTO projects (name, tag, live_url, github_url, start_date, end_date, display_order, is_active)
            VALUES (
                'Plexi', 
                'Production RAG Study Assistant', 
                'https://plexi.mexus.tech/', 
                NULL, 
                'Jan. 2024', 
                'Present', 
                2, 
                1
            )
        """)
        async with db.execute("SELECT last_insert_rowid() as lid") as c:
            p2_id = (await c.fetchone())[0]

        await db.execute("""
            INSERT INTO project_bullets (project_id, bullet, keywords, display_order) VALUES 
            (?, 'Designed an end-to-end document ingestion and RAG pipeline with LlamaIndex and LangChain covering PDF/text ingestion, chunking strategy, embedding generation, vector storage in ChromaDB, and query-time retrieval across 200+ documents.', 'LlamaIndex,LangChain,ChromaDB,RAG,Vector Search', 1),
            (?, 'Implemented multi-agent orchestration with Smolagents, splitting query decomposition, vector store retrieval, and response synthesis across independent agents for domain-specific academic content.', 'Smolagents,Multi-Agent,Query Decomposition', 2),
            (?, 'Evolved from Streamlit monolith (V1) to production microservices (V2: FastAPI retrieval API + Next.js on Cloudflare Workers); exposed RAG capabilities as queryable REST endpoints consumable by any client.', 'FastAPI,Next.js,Cloudflare Workers,REST API', 3)
        """, (p2_id, p2_id, p2_id))

        # Project 3: Chat-with-PDF
        await db.execute("""
            INSERT INTO projects (name, tag, live_url, github_url, start_date, end_date, display_order, is_active)
            VALUES (
                'Chat-with-PDF', 
                'Conversational Document QA System', 
                NULL, 
                'https://github.com/KunalGupta25/chat-with-pdf/', 
                'Nov. 2023', 
                'Jan. 2024', 
                3, 
                1
            )
        """)
        async with db.execute("SELECT last_insert_rowid() as lid") as c:
            p3_id = (await c.fetchone())[0]

        await db.execute("""
            INSERT INTO project_bullets (project_id, bullet, keywords, display_order) VALUES 
            (?, 'Built a document ingestion and conversational RAG pipeline enabling natural language Q&A over user-uploaded PDFs using LangChain, FAISS vector store, and Gemini API as the LLM backbone.', 'LangChain,FAISS,Gemini API,Document QA', 1),
            (?, 'Deployed as a Streamlit web app with session-level isolated vector indices per user, preventing cross-session data leakage across concurrent users.', 'Streamlit,Vector Isolation,Session Management', 2)
        """, (p3_id, p3_id))

        # 6. Experience
        await db.execute("DELETE FROM experience_bullets")
        await db.execute("DELETE FROM experience")

        await db.execute("""
            INSERT INTO experience (role, organization, location, start_date, end_date, display_order)
            VALUES (
                'Coordinator, Career Development Cell',
                'Parul Institute of Technology',
                'Vadodara, Gujarat',
                'July 2024',
                'February 2025',
                1
            )
        """)
        async with db.execute("SELECT last_insert_rowid() as lid") as c:
            exp_id = (await c.fetchone())[0]

        await db.execute("""
            INSERT INTO experience_bullets (experience_id, bullet, keywords, display_order) VALUES
            (?, 'Contributed to technical and content teams for Fun Fest 2024, Gujarat largest non-technical event with 2,000+ participants across 15+ competitions.', 'Event Leadership,Operations', 1),
            (?, 'Managed event registration and data workflow using Google Sheets and Excel, processing 2,000+ records with zero data loss.', 'Data Workflow,Process Management', 2),
            (?, 'Led technical team for Mic Master 2025, Parul University largest speaking event with 500+ participants.', 'Technical Coordination,Team Leadership', 3)
        """, (exp_id, exp_id, exp_id))

        # 7. Certifications
        await db.execute("DELETE FROM certifications")
        certs = [
            ("Building RAG Agents with LLMs", "NVIDIA", "Sep. 2025", 1),
            ("Fundamentals of Agents", "Hugging Face", "May 2025", 2),
            ("AI Infrastructure & Ops Fundamentals", "Coursera", "Jan. 2025", 3),
            ("AWS Cloud Practitioner Essentials", "Coursera", "Aug. 2025", 4),
            ("Software Engineering Virtual Experience", "Skyscanner/Forage", "May 2025", 5),
            ("Computer Networks and Internet Protocol", "NPTEL", "May 2025", 6)
        ]
        for name, issuer, date, order in certs:
            await db.execute("""
                INSERT INTO certifications (name, issuer, issued_date, display_order)
                VALUES (?, ?, ?, ?)
            """, (name, issuer, date, order))

        await db.commit()
        print("✅ fitFolio database successfully seeded with full profile data!")

if __name__ == "__main__":
    asyncio.run(seed())
