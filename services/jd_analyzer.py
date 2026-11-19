from services.gemini import call_gemini_json


async def analyze(jd_text: str) -> dict:
    prompt = f"""Analyze this job description and extract:
1. required_skills: list of strings — skills explicitly marked required/must-have
2. preferred_skills: list of strings — skills marked preferred/nice-to-have/plus/bonus  
3. role_keywords: list of 8-12 strings — key technical terms for ATS optimization
4. seniority: one string — one of: fresher, junior, mid, senior

Job Description:
{jd_text}

Return JSON only. No commentary."""

    result = await call_gemini_json(prompt)
    return {
        "required_skills": result.get("required_skills", []),
        "preferred_skills": result.get("preferred_skills", []),
        "role_keywords": result.get("role_keywords", []),
        "seniority": result.get("seniority", "mid"),
    }
