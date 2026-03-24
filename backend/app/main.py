from fastapi import FastAPI
from app.routers import auth, uploads

app = FastAPI(title="OW_BC Backend", version="0.1.0")

app.include_router(auth.router)
app.include_router(uploads.router)

@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True}
