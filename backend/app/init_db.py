import asyncio
from app.db.session import engine
from app.db.models import __init__  # load all models
from app.db.base import Base
from app.db.models.user import User
from app.db.models.organization import Organization
from app.core.security import hash_password
from sqlalchemy.ext.asyncio import async_sessionmaker

async def init_db():
    print("Creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    print("Creating default organization and user...")
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        org = Organization(name="Default Org")
        session.add(org)
        await session.commit()
        await session.refresh(org)
        
        usr = User(
            email="user3@gmail.com",
            password_hash=hash_password("password123"),
            organization_id=org.id,
            role="admin",
        )
        session.add(usr)
        await session.commit()
        print("Database initialized successfully.")

if __name__ == "__main__":
    asyncio.run(init_db())
