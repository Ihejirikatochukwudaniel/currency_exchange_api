from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# ✅ PostgreSQL connection URL from .env
# Example: postgresql+asyncpg://user:password@host:port/dbname
DATABASE_URL = str(settings.database_url)

# ✅ Create the async SQLAlchemy engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)

# ✅ Create async session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ✅ Base class for models
Base = declarative_base()

# ✅ Dependency to get DB session (for FastAPI routes)
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
