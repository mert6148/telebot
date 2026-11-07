"""API-key authentication example for a compiler service built with FastAPI.

Set COMPILER_API_KEYS to one or more comma-separated, high-entropy secrets.
Clients send the key in the X-API-Key header.
"""

from __future__ import annotations

import hmac
import os
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.security import APIKeyHeader

app = FastAPI(title="Compiler API")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


@lru_cache(maxsize=1)
def configured_api_keys() -> tuple[str, ...]:
    """Load configured keys once; fail closed if none are configured."""
    raw = os.getenv("COMPILER_API_KEYS", "")
    keys = tuple(key.strip() for key in raw.split(",") if key.strip())
    if not keys:
        raise RuntimeError("COMPILER_API_KEYS must contain at least one secret")
    return keys


async def require_compiler_api_key(
    supplied_key: Annotated[str | None, Security(api_key_header)],
) -> None:
    if not supplied_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Compare against every configured key to avoid an early-exit timing leak.
    valid = False
    for expected_key in configured_api_keys():
        valid = hmac.compare_digest(supplied_key, expected_key) or valid

    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )


@app.get("/health")
async def health() -> dict[str, str]:
    """Unauthenticated liveness endpoint; do not return secrets or config."""
    return {"status": "ok"}


@app.post("/compile", dependencies=[Depends(require_compiler_api_key)])
async def compile_code() -> dict[str, str]:
    """Replace this body with the existing compiler implementation."""
    return {"message": "Authenticated. Connect your compiler implementation here."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("compiler_auth:app", host="127.0.0.1", port=8000)
