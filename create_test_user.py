import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models import Base, User

async def create_test_user():
    # Create async engine
    engine = create_async_engine(
        "sqlite+aiosqlite:///tasks.db",
        connect_args={"check_same_thread": False}
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Create test user
    async with async_session() as session:
        test_user = User(
            username="testuser",
            email="test@example.com"
        )
        session.add(test_user)
        await session.commit()
        print(f"Created test user with ID: {test_user.user_id}")

if __name__ == "__main__":
    asyncio.run(create_test_user()) 