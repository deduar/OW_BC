from fastapi import FastAPI

app = FastAPI(title="OW_BC Backend", version="0.1.0")


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True}

