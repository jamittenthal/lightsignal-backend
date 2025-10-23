from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Optional
import os
import time
import jwt
import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import json

# Simple in-memory rate limiter for auth endpoints (per-IP)
_RATE_STORE = {}
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 20

# JWKS cache
_JWKS_CACHE = {}
_JWKS_CACHE_TTL = 300  # 5 minutes


def _rate_check(ip: str) -> bool:
    now = int(time.time())
    rec = _RATE_STORE.get(ip)
    if not rec or rec[0] + RATE_LIMIT_WINDOW < now:
        _RATE_STORE[ip] = (now, 1)
        return True
    ts, count = rec
    if count >= RATE_LIMIT_MAX:
        return False
    _RATE_STORE[ip] = (ts, count + 1)
    return True


def _get_jwks_key(jwks_url: str, kid: str) -> Optional[str]:
    """Fetch and cache JWKS keys, return PEM format for given kid."""
    now = int(time.time())
    cache_key = f"{jwks_url}:{kid}"
    
    # Check cache
    if cache_key in _JWKS_CACHE:
        cached_time, cached_key = _JWKS_CACHE[cache_key]
        if now - cached_time < _JWKS_CACHE_TTL:
            return cached_key
    
    try:
        # Fetch JWKS
        response = requests.get(jwks_url, timeout=10)
        response.raise_for_status()
        jwks = response.json()
        
        # Find matching key
        for key in jwks.get("keys", []):
            if key.get("kid") == kid and key.get("kty") == "RSA":
                # Convert JWK to PEM
                n = jwt.utils.base64url_decode(key["n"])
                e = jwt.utils.base64url_decode(key["e"])
                
                # Create RSA public key
                public_numbers = rsa.RSAPublicNumbers(
                    int.from_bytes(e, byteorder="big"),
                    int.from_bytes(n, byteorder="big")
                )
                public_key = rsa.RSAPublicKey(public_numbers)
                pem_key = public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ).decode()
                
                # Cache and return
                _JWKS_CACHE[cache_key] = (now, pem_key)
                return pem_key
                
    except Exception as e:
        print(f"JWKS fetch error: {e}")
        return None
    
    return None


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware enforcing auth and tenancy per spec.

    Rules:
    - If company_id == 'demo' -> allow, stamp _meta.demo = True
    - Else require Authorization: Bearer <jwt> or cookie 'session'
      - verify JWT with JWKS (if AUTH_JWKS_URL set) or HS256 with secret from AUTH_JWT_SECRET
      - 401 -> "Login required"
      - 403 -> "Unauthorized for this company" when token.company_id != req.company_id

    Also injects _meta.tenant and _meta.demo into JSON dict responses for /api/*
    
    Environment variables:
    - AUTH_DISABLED: if "true", bypass all auth checks (dev mode)
    - AUTH_JWKS_URL: JWKS endpoint for RSA key verification (Auth0/GCP/Azure)
    - AUTH_JWT_SECRET: HS256 secret for local verification (fallback)
    """

    def __init__(self, app):
        super().__init__(app)
        self.auth_disabled = os.environ.get("AUTH_DISABLED", "false").lower() == "true"
        self.jwks_url = os.environ.get("AUTH_JWKS_URL")
        self.jwt_secret = os.environ.get("AUTH_JWT_SECRET", "dev-secret")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        
        # Development bypass
        if self.auth_disabled:
            request.state._meta_demo = True  # treat as demo when disabled
            request.state.tenant = "demo"
            resp = await call_next(request)
            return await _inject_meta(resp, "demo", True)
        
        # Only protect API business endpoints under /api/
        if not path.startswith("/api/"):
            return await call_next(request)

        # Extract company_id from body (if JSON) or from path/query
        company_id: Optional[str] = None

        # Attempt to get from path params if provided (FastAPI populates scope['path_params'])
        try:
            path_params = request.scope.get("path_params", {}) or {}
            company_id = path_params.get("company_id")
        except Exception:
            company_id = None

        # If still not present, try query params
        if not company_id:
            company_id = request.query_params.get("company_id")

        # If still not present, try JSON body
        body = None
        if not company_id and request.method in ("POST", "PUT", "PATCH"):
            try:
                body = await request.json()
                if isinstance(body, dict):
                    company_id = body.get("company_id")
            except Exception:
                # not JSON or empty
                body = None

        company_id = company_id or "demo"

        # Demo bypass
        is_demo = company_id == "demo"
        if is_demo:
            # stamp into scope for handlers
            request.state._meta_demo = True
            request.state.tenant = company_id
            # call handlers normally
            resp = await call_next(request)
            return await _inject_meta(resp, company_id, True)

        # Non-demo: require token
        # rate limit auth checks per client IP (best-effort)
        client_ip = request.client.host if request.client else "unknown"
        if not _rate_check(client_ip):
            return JSONResponse(status_code=429, content={"detail": "Too many requests"})

        auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
        token = None
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header.split(None, 1)[1].strip()
        else:
            # fallback to cookie named 'session'
            token = request.cookies.get("session")

        if not token:
            return JSONResponse(status_code=401, content={"detail": "Login required"})

        # Verify token with JWKS or HS256
        payload = None
        
        if self.jwks_url:
            # Try JWKS verification first
            try:
                # Decode header to get kid
                header = jwt.get_unverified_header(token)
                kid = header.get("kid")
                
                if kid:
                    public_key = _get_jwks_key(self.jwks_url, kid)
                    if public_key:
                        payload = jwt.decode(token, public_key, algorithms=["RS256"])
                    else:
                        # Fall back to HS256 if JWKS fails
                        payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
                else:
                    # No kid, try HS256
                    payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
                    
            except jwt.exceptions.InvalidTokenError:
                # Try HS256 as fallback
                try:
                    payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
                except jwt.exceptions.InvalidTokenError:
                    return JSONResponse(status_code=401, content={"detail": "Login required"})
        else:
            # Only HS256 verification
            try:
                payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            except jwt.exceptions.InvalidTokenError:
                return JSONResponse(status_code=401, content={"detail": "Login required"})

        token_cid = payload.get("company_id")
        if token_cid != company_id:
            return JSONResponse(status_code=403, content={"detail": "Unauthorized for this company"})

        # stamp user info into request.state and proceed
        request.state.user = payload
        request.state.tenant = company_id
        request.state._meta_demo = False

        resp = await call_next(request)
        return await _inject_meta(resp, company_id, False)


async def _inject_meta(resp: Response, company_id: str, is_demo: bool) -> Response:
    """If response is JSON and top-level dict, ensure _meta.tenant and _meta.demo present."""
    # Only try to mutate JSON responses
    content_type = resp.headers.get("content-type", "")
    if "application/json" not in content_type:
        return resp

    # Read body bytes
    body = b""
    async for chunk in resp.body_iterator:
        body += chunk

    # Recreate response if parsing succeeds
    try:
        import json

        data = json.loads(body.decode("utf-8"))
        if isinstance(data, dict):
            meta = data.get("_meta") or {}
            meta.setdefault("tenant", company_id)
            meta.setdefault("demo", is_demo)
            data["_meta"] = meta
            new_body = json.dumps(data).encode("utf-8")
            # build new response
            new_resp = Response(content=new_body, status_code=resp.status_code, media_type="application/json")
            return new_resp
    except Exception:
        # if anything goes wrong, return original response
        pass

    # fallback: return original
    return resp
