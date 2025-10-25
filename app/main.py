from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routers import countries
from app.database import engine, Base, close_engine

# ✅ Use lifespan context manager (recommended over deprecated on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables created successfully.")
    except Exception as e:
        print(f"❌ Database connection error during startup: {e}")
        # Don't raise - let the app start even if DB fails
    
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

# ✅ Healthcheck endpoint - FIXED TYPO
@app.get("/kaithhealthcheck")
async def healthcheck():
    return {"status": "ok"}

# ✅ Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to Country Cache API"}

# ✅ Only for local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True
    )
