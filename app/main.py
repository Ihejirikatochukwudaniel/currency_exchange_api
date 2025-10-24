from fastapi import FastAPI
from app.routers import countries
from app.database import engine, Base
import asyncio

app = FastAPI(title="Country Cache API", version="1.0")
app.include_router(countries.router)

@app.on_event('startup')
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get('/')
async def root():
    return {"message": "Welcome to Country Cache API"}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app.main:app', host='0.0.0.0', port=8000, reload=True)