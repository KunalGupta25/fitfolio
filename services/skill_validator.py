from __future__ import annotations

import aiosqlite
from services.gemini import call_gemini_json

# Difficulty tiers for ranking skills
DIFFICULTY: dict[str, list[str]] = {
    "hard": [
        "machine learning", "deep learning", "reinforcement learning",
        "distributed systems", "kubernetes", "compilers", "operating systems",
        "cryptography", "computer vision", "nlp", "natural language processing",
        "rust", "c++", "assembly", "cuda", "gpu programming", "system design",
        "data structures", "algorithms", "competitive programming",
    ],
    "medium": [
        "python", "java", "javascript", "typescript", "golang", "c#",
        "react", "angular", "vue", "node.js", "django", "fastapi", "flask",
        "sql", "postgresql", "mysql", "mongodb", "redis", "docker",
        "aws", "azure", "gcp", "git", "ci/cd", "rest api", "graphql",
        "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
    ],
    "easy": [
        "html", "css", "bash", "linux", "excel", "powerpoint",
        "figma", "jira", "confluence", "slack", "trello", "notion",
        "communication", "teamwork", "agile", "scrum",
    ],
}


def _tier(skill_name: str) -> int:
    """Return sort key: 0=hard, 1=medium, 2=easy, 3=unknown."""
    lower = skill_name.lower()
    for tier, names in DIFFICULTY.items():
        if any(lower == n or lower in n or n in lower for n in names):
            return {"hard": 0, "medium": 1, "easy": 2}[tier]
    return 3


def rank_by_difficulty(skill_names: list[str]) -> list[str]:
    return sorted(skill_names, key=_tier)


def pick_hardest_three(skill_names: list[str]) -> list[str]:
    return rank_by_difficulty(skill_names)[:3]


async def generate_single_test(skill_name: str) -> list[dict]:
    prompt = f"""Create a 3-question technical knowledge test for the skill: {skill_name}

Each question must assess a different aspect of the skill (concept, application, troubleshooting).
Return a JSON array of exactly 3 objects, each with keys:
- "question": the question text (1-2 sentences)
- "aspect": one of "concept", "application", "troubleshooting"

Example format:
[
  {{"question": "What is ...", "aspect": "concept"}},
  {{"question": "How would you ...", "aspect": "application"}},
  {{"question": "If ... fails, what do you check first?", "aspect": "troubleshooting"}}
]

Return JSON array only. No commentary."""

    result = await call_gemini_json(prompt)
    if isinstance(result, list):
        return result
    return []


async def generate_bulk_test(skill_names: list[str]) -> dict:
    top_three = pick_hardest_three(skill_names)

    prompt = f"""Create a combined technical test covering these skills: {", ".join(top_three)}

Generate 2 questions per skill (6 questions total). Each question must specify which skill it tests.
Return a JSON object with:
- "selected_skills": list of the skill names tested
- "questions": list of objects, each with:
  - "question": question text
  - "aspect": one of "concept", "application", "troubleshooting"
  - "skill": which skill this question tests

Return JSON only. No commentary."""

    result = await call_gemini_json(prompt)
    if isinstance(result, dict):
        return {
            "selected_skills": result.get("selected_skills", top_three),
            "questions": result.get("questions", []),
        }
    return {"selected_skills": top_three, "questions": []}


async def grade_answers(
    skill_name: str,
    questions: list[str],
    answers: list[str],
) -> dict:
    qa_pairs = "\n".join(
        f"Q{i+1}: {q}\nA{i+1}: {a}" for i, (q, a) in enumerate(zip(questions, answers))
    )

    prompt = f"""Grade these answers for a technical test on: {skill_name}

{qa_pairs}

Evaluate each answer on a scale of 0-100 and determine if the candidate passed (overall >= 60).
Return a JSON object with:
- "scores": list of integers (one per question, 0-100)
- "overall_score": float (average, 0-100)
- "passed": boolean (true if overall_score >= 60)
- "feedback": string (2-3 sentences of constructive feedback)

Return JSON only. No commentary."""

    try:
        result = await call_gemini_json(prompt)
        if isinstance(result, dict):
            scores = result.get("scores", [])
            overall = result.get("overall_score", sum(scores) / len(scores) if scores else 0.0)
            return {
                "scores": scores,
                "overall_score": float(overall),
                "passed": result.get("passed", float(overall) >= 60),
                "feedback": result.get("feedback", ""),
            }
    except Exception as e:
        return {"scores": [], "overall_score": 0.0, "passed": False, "feedback": f"Grading error: {str(e)}"}

    return {"scores": [], "overall_score": 0.0, "passed": False, "feedback": "Grading failed."}


async def grade_and_store(
    arg1: int | str,
    arg2: int | str | list[str],
    arg3: list[str] | int | None = None,
    db: aiosqlite.Connection | None = None,
) -> dict:
    """Flexible helper supporting both:
    grade_and_store(skill_name, answers, skill_id, db) AND
    grade_and_store(skill_id, skill_name, answers, db)
    """
    if isinstance(arg1, int):
        skill_id = arg1
        skill_name = str(arg2)
        answers = arg3 if isinstance(arg3, list) else []
    else:
        skill_name = str(arg1)
        answers = arg2 if isinstance(arg2, list) else []
        skill_id = int(arg3) if isinstance(arg3, int) else 0

    # Generate reference questions
    questions_data = await generate_single_test(skill_name)
    questions = [q["question"] for q in questions_data] if questions_data else [f"Explain your experience with {skill_name}"]

    result = await grade_answers(skill_name, questions, answers)

    validated = 1 if result["passed"] else -1
    if db:
        await db.execute(
            "UPDATE skills SET validated = ?, test_score = ? WHERE id = ?",
            (validated, result["overall_score"], skill_id),
        )
        await db.commit()

    return result


async def grade_bulk_and_store(
    skill_ids: list[int],
    selected_skills: list[str],
    answers: list[str],
    db: aiosqlite.Connection,
) -> dict:
    prompt = f"""Grade these technical test answers covering skills: {", ".join(selected_skills)}

Answers provided:
{chr(10).join(f"- Answer {i+1}: {a}" for i, a in enumerate(answers))}

Evaluate if the candidate demonstrates competency (pass threshold: 60/100).
Return JSON object:
- "overall_score": float (0-100)
- "passed": boolean
- "feedback": string (1-2 sentences)"""

    try:
        result = await call_gemini_json(prompt)
        passed = result.get("passed", False)
        score = float(result.get("overall_score", 0.0))
        feedback = result.get("feedback", "")
    except Exception:
        passed = False
        score = 0.0
        feedback = "Bulk grading failed."

    validated = 1 if passed else 0
    for sid in skill_ids:
        await db.execute(
            "UPDATE skills SET validated = ?, test_score = ? WHERE id = ?",
            (validated, score, sid),
        )
    await db.commit()

    return {
        "passed": passed,
        "overall_score": score,
        "feedback": feedback,
        "updated_count": len(skill_ids),
    }
