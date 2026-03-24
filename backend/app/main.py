from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, uploads, reconciliation, audit
from app.config import settings

app = FastAPI(title="OW_BC Backend", version="0.1.0")

# 10.2 Implement strict CORS configuration and security headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.CORS_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

app.include_router(auth.router)
app.include_router(uploads.router)
app.include_router(reconciliation.router)
app.include_router(audit.router)

@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True}
