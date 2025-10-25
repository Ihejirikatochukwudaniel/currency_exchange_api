from fastapi import FastAPI
from app.routers import countries
from app.database import engine, Base, close_engine
import asyncio

app = FastAPI(
    title="Country Cache API",
    version="1.0",
    description="An API that caches country data and exchange rates."
)

# ✅ Register routers
app.include_router(countries.router)

# ✅ Healthcheck endpoint (Leapcell expects this)
@app.get("/kaithhealthcheck")
async def healthcheck():
    return {"status": "ok"}

# ✅ Create database tables (non-blocking)
@app.on_event("startup")
async def on_startup():
    async def init_db():
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("✅ Database tables created successfully.")
        except Exception as e:
            print(f"❌ Database connection error during startup: {e}")

    # Run DB initialization in the background (non-blocking)
    asyncio.create_task(init_db())

# ✅ Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to Country Cache API"}

# ✅ Graceful shutdown
@app.on_event("shutdown")
async def on_shutdown():
    try:
        await close_engine()
        print("🛑 Database engine disposed successfully.")
    except Exception as e:
        print(f"⚠️ Error disposing database engine: {e}")

# ✅ Only for local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True
    )
