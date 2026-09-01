from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.config import settings
from app.routers import auth, items, categories, locations, movements, dashboard, alerts, importexport, users

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Inventory & Stock Control API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(locations.router)
app.include_router(items.router)
app.include_router(movements.router)
app.include_router(dashboard.router)
app.include_router(alerts.router)
app.include_router(importexport.router)
app.include_router(users.router)


@app.get("/")
def root():
    return {
        "message": "Inventory & Stock Control API",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
def health():
    return {"status": "ok"}