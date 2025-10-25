from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routers import countries
from app.database import engine, Base, close_engine
import asyncio

# ✅ Global flag to track DB initialization status
db_ready = False
db_error = None

async def init_database():
    """Initialize database tables in the background"""
    global db_ready, db_error
    try:
        print("🔄 Starting database initialization...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        db_ready = True
        print("✅ Database tables created successfully.")
    except Exception as e:
        db_error = str(e)
        print(f"❌ Database connection error during startup: {e}")

# ✅ Use lifespan context manager but don't block startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - Initialize DB in background (non-blocking)
    asyncio.create_task(init_database())
    print("🚀 App starting (DB initializing in background)...")
    
    yield  # App is running
    
    # Shutdown
    try:
        await close_engine()
        print("🛑 Database engine disposed successfully.")
    except Exception as e:
        print(f"⚠️ Error disposing database engine: {e}")

app = FastAPI(
    title="Country Cache API",
    version="1.0",
    description="An API that caches country data and exchange rates.",
    lifespan=lifespan
)

# ✅ Register routers
app.include_router(countries.router)

# ✅ Healthcheck endpoint - Returns immediately without waiting for DB
@app.get("/kaithhealthcheck")
async def healthcheck():
    """
    Health check endpoint for Leapcell proxy.
    Returns 200 immediately, even if database is still initializing.
    """
    return {
        "status": "ok",
        "database_ready": db_ready,
        "database_error": db_error
    }

# ✅ Readiness check - Shows if app is ready to handle requests
@app.get("/ready")
async def readiness():
    """
    Readiness check - returns 200 only when database is ready.
    Use this to check if the app can handle actual requests.
    """
    if not db_ready:
        if db_error:
            return {
                "status": "not_ready",
                "reason": f"Database initialization failed: {db_error}"
            }, 503
        return {
            "status": "not_ready", 
            "reason": "Database is still initializing"
        }, 503
    
    return {
        "status": "ready",
        "database_ready": True
    }

# ✅ Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to Country Cache API",
        "database_ready": db_ready,
        "endpoints": {
            "health": "/kaithhealthcheck",
            "readiness": "/ready",
            "countries": "/countries",
            "docs": "/docs"
        }
    }

# ✅ Only for local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True
    )
