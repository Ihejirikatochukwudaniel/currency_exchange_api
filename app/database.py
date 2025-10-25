import ssl
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# ✅ Database URL (from .env)
DATABASE_URL = str(settings.database_url)

# ✅ Create an SSL context for secure PostgreSQL connection
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE  # Leapcell handles SSL internally

# ✅ Build async SQLAlchemy engine with connection pool tuning
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    connect_args={"ssl": ssl_context},
    pool_pre_ping=True,       # checks connections before using them
    pool_recycle=300,         # recycle connections every 5 minutes
    pool_timeout=30,          # max wait time for connection (seconds)
)

# ✅ Create async session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ✅ Base class for ORM models
Base = declarative_base()

# ✅ Dependency for FastAPI routes
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            # ✅ ensure the session is explicitly closed
            await session.close()

# ✅ Optional: Graceful shutdown handler to close the engine
async def close_engine():
    await engine.dispose()
