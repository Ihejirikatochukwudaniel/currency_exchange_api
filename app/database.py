from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# Get the database URL from your environment
DATABASE_URL = settings.database_url

# Create the async engine
engine = create_async_engine(DATABASE_URL, echo=False, future=True)

# Create the session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Declare the base for ORM models
Base = declarative_base()

# ✅ Dependency for FastAPI
async def get_db():
    """
    Dependency that provides a SQLAlchemy async session.
    Closes the session automatically after request.
    """
    async with AsyncSessionLocal() as session:
        yield session
