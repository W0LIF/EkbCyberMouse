from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from api.app.routers import reference, plan, events
from api.app.models import Health

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
app.include_router(events.router, prefix="/api/v1")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    import traceback
    tb = traceback.format_exc()
    try:
        with open("C:/Githab/EkbCyberMouse/backend/server_error.log", "w", encoding="utf-8") as f:
            f.write(f"{request.method} {request.url}\n{tb}")
    except Exception:
        pass
    return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL", "message": str(exc)[:1000], "details": []}})


@app.get("/api/v1/health", response_model=Health)
def health_check():
    return {"status": "ok", "team": "EkbCyberMouse", "version": "1.0.0"}