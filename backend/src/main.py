from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.config import settings
from src.database.init_db import init_database
from src.routers import admin, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_database()
    yield
    # Shutdown (if needed)


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Backend API for organizing collective recitation of Quran and Islamic texts",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(admin.router)


@app.get("/")
async def root():
    return {"message": settings.app_name, "version": settings.version, "docs": "/docs"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
