import ssl
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# ✅ Your Leapcell PostgreSQL connection URL
DATABASE_URL = str(settings.database_url)  # from .env

# ✅ Create an SSL context for secure PostgreSQL connection
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE  # Leapcell handles SSL verification internally

# ✅ Build async SQLAlchemy engine using asyncpg driver
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    connect_args={"ssl": ssl_context},  # ✅ correct way to pass SSL for asyncpg
)

# ✅ Create async session
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ✅ Base class for models
Base = declarative_base()

# ✅ Dependency to get DB session (for FastAPI)
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
