from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# ✅ PostgreSQL connection URL from .env (Leapcell)
# Example:
# postgresql+asyncpg://ejtqlxfhbngocjoyqxrm:euicntkqjcqpalrbnjijxserlcasdf@9qasp5v56q8ckkf5dc.apn.leapcellpool.com:6438/wbdqnnvdgnztlomqqfcu?sslmode=require
DATABASE_URL = str(settings.database_url).replace("postgresql://", "postgresql+asyncpg://")

# ✅ Create async engine (Leapcell manages SSL automatically)
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

# ✅ Base model for all tables
Base = declarative_base()

# ✅ Dependency for FastAPI routes
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
