from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

engine = create_async_engine(settings.effective_database_url, echo=True)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# Automatic table creation for SQLite (for tests only)
if settings.effective_database_url.startswith("sqlite"):
    async def create_all():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)