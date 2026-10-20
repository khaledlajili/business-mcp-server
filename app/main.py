from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router as api_router
from app.config import settings
from app.database import engine
from app.mcp_server import mcp
from mcp.server.transport_security import TransportSecuritySettings


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
    expose_headers=["Mcp-Session-Id"],
)


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal error: {type(exc).__name__}: {exc}"},
        headers={"Access-Control-Allow-Origin": "*"},
    )


app.include_router(api_router)

public_host = (
    settings.mcp_public_url.replace("https://", "").replace("http://", "").split("/")[0]
    if settings.mcp_public_url
    else ""
)
allowed_hosts = ["localhost", "localhost:*", "127.0.0.1", "127.0.0.1:*"]
if public_host and public_host not in allowed_hosts:
    allowed_hosts.extend([public_host, f"{public_host}:*"])

allowed_origins = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
if public_host:
    allowed_origins.append(f"https://{public_host}")

security = TransportSecuritySettings(
    allowed_hosts=allowed_hosts,
    allowed_origins=allowed_origins,
)

app.mount(
    "/mcp",
    mcp.streamable_http_app(
        stateless_http=True,
        streamable_http_path="/",
        transport_security=security,
    ),
)


@app.get("/health")
async def health():
    return {"status": "ok", "environment": settings.environment}
