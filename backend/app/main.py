import time
import logging
import json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, uploads, reconciliation, audit
from app.config import settings

app = FastAPI(title="OW_BC Backend", version="0.1.0")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("owbc")

# Middleware for security headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Middleware for structured logging and timing
@app.middleware("http")
async def log_request_time(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    log_data = {
        "method": request.method,
        "url": str(request.url),
        "duration": f"{process_time:.4f}s",
        "status_code": response.status_code,
        "client": request.client.host if request.client else "unknown"
    }
    logger.info(json.dumps(log_data))
    
    response.headers["X-Process-Time"] = str(process_time)
    return response

# 10.2 Implement strict CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.CORS_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(uploads.router, prefix="/api")
app.include_router(reconciliation.router, prefix="/api")
app.include_router(audit.router, prefix="/api")

@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True}
