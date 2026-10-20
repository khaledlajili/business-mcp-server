from fastapi import HTTPException, status
from app.config import settings

READ_SCOPES = {"customers:read", "orders:read", "inventory:read", "sales:read"}
WRITE_SCOPES = READ_SCOPES | {"quotes:write", "tickets:write"}

TOKEN_SCOPES = {
    settings.mcp_read_token: READ_SCOPES,
    settings.mcp_write_token: WRITE_SCOPES,
}


def get_scopes_for_token(token: str) -> set[str] | None:
    return TOKEN_SCOPES.get(token)


def require_scope(token: str, required: str) -> None:
    scopes = get_scopes_for_token(token)
    if scopes is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    if required not in scopes:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Missing scope: {required}")
