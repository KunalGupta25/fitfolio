import asyncio
from core.database import init_db, get_db

async def main():
    await init_db()
    print("Database tables initialized successfully!")

    async for db in get_db():
        async with db.execute("SELECT name FROM sqlite_master WHERE type='table'") as c:
            tables = [r[0] for r in await c.fetchall()]
            print("Tables found in fitfolio.db:", sorted(tables))
        break

if __name__ == "__main__":
    asyncio.run(main())
