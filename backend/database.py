from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from config import settings

client: AsyncIOMotorClient | None = None
db: AsyncIOMotorDatabase | None = None


async def connect_db() -> AsyncIOMotorDatabase | None:
    global client, db
    try:
        client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=3000)
        db = client[settings.mongodb_db]
        await db.command("ping")
        return db
    except Exception:
        if client:
            client.close()
        client = None
        db = None
        return None


async def close_db() -> None:
    global client, db
    if client:
        client.close()
    client = None
    db = None


def get_db() -> AsyncIOMotorDatabase:
    if db is None:
        raise RuntimeError("MongoDB bağlantısı yok.")
    return db
