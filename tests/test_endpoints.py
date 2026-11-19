import asyncio
import httpx
from main import app

async def test_routes():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test", follow_redirects=True) as client:
        # 1. Health check
        res = await client.get("/health")
        print("GET /health ->", res.status_code, res.json())
        assert res.status_code == 200

        # 2. Dashboard HTML page
        res = await client.get("/", headers={"accept": "text/html"})
        print("GET / (Dashboard HTML) ->", res.status_code, "Length:", len(res.text))
        assert res.status_code == 200
        assert "Profile Completeness" in res.text

        # 3. Profile page
        res = await client.get("/profile", headers={"accept": "text/html"})
        print("GET /profile (HTML) ->", res.status_code)
        assert res.status_code == 200

        # 4. Save personal info
        res = await client.post("/profile/personal", json={
            "full_name": "Kunal Gupta",
            "phone": "+91 9999999999",
            "email": "kunal@example.com",
            "city": "Vadodara",
            "state": "Gujarat"
        })
        print("POST /profile/personal ->", res.status_code)
        assert res.status_code in (200, 201)

        # 5. Skills page
        res = await client.get("/skills", headers={"accept": "text/html"})
        print("GET /skills (HTML) ->", res.status_code)
        assert res.status_code == 200

        # 6. Projects page
        res = await client.get("/projects", headers={"accept": "text/html"})
        print("GET /projects (HTML) ->", res.status_code)
        assert res.status_code == 200

        # 7. Experience page
        res = await client.get("/experience", headers={"accept": "text/html"})
        print("GET /experience (HTML) ->", res.status_code)
        assert res.status_code == 200

        # 8. Education page
        res = await client.get("/education", headers={"accept": "text/html"})
        print("GET /education (HTML) ->", res.status_code)
        assert res.status_code == 200

        # 9. Certifications page
        res = await client.get("/certifications", headers={"accept": "text/html"})
        print("GET /certifications (HTML) ->", res.status_code)
        assert res.status_code == 200

        # 10. Resume page
        res = await client.get("/resume", headers={"accept": "text/html"})
        print("GET /resume (HTML) ->", res.status_code)
        assert res.status_code == 200

        print("\n ALL FASTAPI ROUTES & TEMPLATES VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(test_routes())
