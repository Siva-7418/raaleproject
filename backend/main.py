from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from backend.app.api.routes_identities import router as identities_router
from backend.app.api.routes_entitlements import router as entitlements_router
from backend.app.api.routes_reviews import router as reviews_router
from backend.app.api.routes_rules import router as rules_router
from backend.app.api.routes_audit import router as audit_router
from backend.app.db.database import init_db

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    title="Evidence-Based Access Review API",
    description="Backend service for contextualized entitlement review, rules engine, and decision auditing.",
    version="1.0.0"
)

# Initialize Database on Startup
@app.on_event("startup")
def startup_event():
    init_db()

# Include API Routers
app.include_router(identities_router)
app.include_router(entitlements_router)
app.include_router(reviews_router)
app.include_router(rules_router)
app.include_router(audit_router)

# Mount Static Frontend
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/")
def read_root():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Evidence-Based Access Review API is running. Access API docs at /docs."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
