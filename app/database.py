from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from app.config import settings

# ✅ Database URL (from .env)
# Change driver from asyncpg to psycopg (async version of psycopg2)
DATABASE_URL = str(settings.database_url)

# Replace asyncpg with psycopg if needed
if "asyncpg" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("asyncpg", "psycopg")
    print("🔄 Switched driver from asyncpg to psycopg")

# ✅ Ensure URL has SSL mode parameter
if "?" not in DATABASE_URL:
    DATABASE_URL = f"{DATABASE_URL}?sslmode=require"
elif "ssl" not in DATABASE_URL.lower():
    DATABASE_URL = f"{DATABASE_URL}&sslmode=require"

print(f"🔗 Connecting to database with psycopg driver")

# ✅ Build async SQLAlchemy engine for Leapcell
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    poolclass=NullPool,  # No connection pooling - Leapcell pooler handles it
    connect_args={
        "connect_timeout": 30,
        "options": "-c search_path=public",  # Set default schema
    },
)

print("✅ Database engine created with psycopg and SSL")

# ✅ Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# ✅ Base class for ORM models
Base = declarative_base()

# ✅ Dependency for FastAPI routes
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()

# ✅ Graceful shutdown handler
async def close_engine():
    await engine.dispose()
    print("✅ Database engine disposed")
