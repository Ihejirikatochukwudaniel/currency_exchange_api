from fastapi import FastAPI
from app.routers import countries
from app.database import engine, Base
import asyncio

app = FastAPI(
    title="Country Cache API",
    version="1.0",
    description="An API that caches country data and exchange rates."
)

# ✅ Register routers
app.include_router(countries.router)

# ✅ Create database tables on startup
@app.on_event("startup")
async def startup():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables created successfully.")
    except Exception as e:
        print(f"❌ Database connection error: {e}")

# ✅ Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to Country Cache API"}

# ✅ Optional: graceful shutdown
@app.on_event("shutdown")
async def shutdown_event():
    await engine.dispose()
    print("🛑 Database engine disposed.")

# ✅ Run the server (only when run directly)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
