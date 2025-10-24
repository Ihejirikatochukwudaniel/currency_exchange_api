import ssl
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# ✅ Your Aiven MySQL connection URL
DATABASE_URL = settings.database_url  # from .env

# ✅ Create an SSL context (required by Aiven)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = True
ssl_context.verify_mode = ssl.CERT_REQUIRED

# ✅ Build the async SQLAlchemy engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    connect_args={"ssl": ssl_context},  # 👈 FIXED HERE
)

# ✅ Create async session
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# ✅ Base class for models
Base = declarative_base()

# ✅ Dependency to get DB session
async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
