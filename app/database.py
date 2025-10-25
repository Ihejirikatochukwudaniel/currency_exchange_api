import ssl
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings

# ✅ Database URL (from .env)
DATABASE_URL = str(settings.database_url)

# ✅ Create an SSL context for secure PostgreSQL connection
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE  # Leapcell handles SSL internally

# ✅ Detect if using connection pooler (port 6438 or 6543 typically)
is_pooler = ":6438" in DATABASE_URL or ":6543" in DATABASE_URL

# ✅ Build async SQLAlchemy engine with proper pooler settings
if is_pooler:
    print("🔵 Using connection pooler configuration")
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        future=True,
        connect_args={
            "ssl": ssl_context,
            "server_settings": {
                "application_name": "country_cache_api",
                # Don't set timeouts with pooler - it manages them
            },
            "timeout": 10,  # Connection timeout
        },
        # ✅ CRITICAL: Disable connection pooling when using external pooler
        poolclass=None,  # No SQLAlchemy pooling - pooler handles it
    )
else:
    print("🟢 Using direct connection configuration")
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        future=True,
        connect_args={
            "ssl": ssl_context,
            "server_settings": {
                "application_name": "country_cache_api",
                "statement_timeout": "30000",  # 30 second query timeout
                "idle_in_transaction_session_timeout": "60000",  # 60 sec idle timeout
            },
            "command_timeout": 30,
            "timeout": 10,  # Connection timeout
        },
        pool_pre_ping=True,       # checks connections before using them
        pool_size=5,              # number of connections to maintain
        max_overflow=10,          # additional connections allowed
        pool_recycle=3600,        # recycle connections every 1 hour
        pool_timeout=30,          # max wait time for connection (seconds)
    )

# ✅ Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,  # Prevent automatic flushes
    autocommit=False,
)

# ✅ Base class for ORM models
Base = declarative_base()

# ✅ Dependency for FastAPI routes
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()  # Commit if successful
        except Exception as e:
            await session.rollback()  # Rollback on error
            raise  # Re-raise the exception
        finally:
            await session.close()  # Always close

# ✅ Graceful shutdown handler to close the engine
async def close_engine():
    await engine.dispose()
