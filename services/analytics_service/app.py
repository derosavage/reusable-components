from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.config import settings
from .routes import router

app = FastAPI(title="Analytics Service", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(router, prefix=f"{settings.API_PREFIX}/analytics")

@app.get("/health")
def health():
    return {"status": "ok", "service": "analytics"}
