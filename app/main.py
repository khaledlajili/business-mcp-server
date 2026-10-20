from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router as api_router
from app.config import settings
from app.database import engine
from app.mcp_server import mcp


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp.session_manager.run():
        yield
    await engine.dispose()


app = FastAPI(
    title="Northstar Trading API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal error: {type(exc).__name__}: {exc}"},
        headers={"Access-Control-Allow-Origin": "*"},
    )


app.include_router(api_router)

# MCP Streamable HTTP — allow the public hostname (set MCP_PUBLIC_URL on Render)
from mcp.server.transport_security import TransportSecuritySettings

public_host = settings.mcp_public_url.replace("https://", "").replace("http://", "").split("/")[0]
security = TransportSecuritySettings(
    allowed_hosts=[public_host, f"{public_host}:*"] if public_host else ["localhost", "127.0.0.1"],
)

app.mount("/mcp", mcp.streamable_http_app(
    streamable_http_path="/",
    transport_security=security,
))


@app.get("/health")
async def health():
    return {"status": "ok", "environment": settings.environment}
