from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection, init_default_sources
from app.api import deals, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    print("Connecting to MongoDB...")
    await connect_to_mongo()
    await init_default_sources()
    print("Connected to MongoDB!")
    
    yield
    
    # Shutdown
    await close_mongo_connection()


# Create FastAPI app
app = FastAPI(
    title="DealBro API",
    description="Hosting deals aggregator API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
origins = settings.cors_origins.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(deals.router, prefix="/api", tags=["deals"])


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "DealBro API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
