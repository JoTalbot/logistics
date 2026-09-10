from fastapi import FastAPI

app = FastAPI(title="AI Logistics OS", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "logistics-api"}


@app.get("/api/v1")
def api_info() -> dict[str, str]:
    return {"version": "v1", "mode": "skeleton"}
