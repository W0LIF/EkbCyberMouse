from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.app.routers import reference, plan

app = FastAPI(title="RTK Dispatch API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reference.router, prefix="/api/v1")
app.include_router(plan.router, prefix="/api/v1")

@app.get("/api/v1/health")
def health_check():
    return {"status": "ok"}