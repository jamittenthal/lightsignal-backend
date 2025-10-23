# Authentication Enhancement Documentation

## Overview

The authentication system has been enhanced with comprehensive support for modern OAuth providers and development workflows.

## Features Added

### 1. JWKS (JSON Web Key Set) Support
- Supports Auth0, Google, Azure AD, and other OIDC providers
- Automatic RSA public key fetching and caching
- Falls back to HS256 local verification if JWKS fails

### 2. Environment Configuration
- `AUTH_DISABLED=true` - Bypasses all auth in development
- `AUTH_JWKS_URL` - JWKS endpoint for RSA verification
- `AUTH_JWT_SECRET` - HS256 secret for local verification

### 3. Comprehensive Test Coverage
- 16 test scenarios covering all auth flows
- 401/403/429 error handling
- Rate limiting behavior
- Token validation edge cases

## Configuration Examples

### Development Mode (No Auth)
```bash
export AUTH_DISABLED=true
# All /api/* requests treated as demo mode
```

### Auth0 Configuration
```bash
export AUTH_JWKS_URL=https://your-domain.auth0.com/.well-known/jwks.json
export AUTH_JWT_SECRET=fallback-secret
```

### Google OAuth Configuration  
```bash
export AUTH_JWKS_URL=https://www.googleapis.com/oauth2/v3/certs
export AUTH_JWT_SECRET=fallback-secret
```

### Azure AD Configuration
```bash
export AUTH_JWKS_URL=https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys
export AUTH_JWT_SECRET=fallback-secret
```

### Local HS256 Only
```bash
export AUTH_JWT_SECRET=your-256-bit-secret
# JWKS_URL not set = HS256 only
```

## Authentication Flow

1. **Demo Bypass**: `company_id == "demo"` → Allow without auth
2. **Token Extraction**: Authorization header or session cookie
3. **JWKS Verification**: If `AUTH_JWKS_URL` set:
   - Fetch RSA public key using token's `kid`
   - Verify with RS256
   - Fall back to HS256 if JWKS fails
4. **HS256 Verification**: Use `AUTH_JWT_SECRET` 
5. **Tenancy Check**: `token.company_id == request.company_id`
6. **Rate Limiting**: 20 auth attempts per IP per minute

## Response Metadata

All `/api/*` JSON responses include:
```json
{
  "data": "...",
  "_meta": {
    "tenant": "company_id",
    "demo": true/false,
    "source": "...",
    "confidence": "..."
  }
}
```

## Error Responses

### 401 Unauthorized
```json
{"detail": "Login required"}
```

### 403 Forbidden  
```json
{"detail": "Unauthorized for this company"}
```

### 429 Rate Limited
```json
{"detail": "Too many requests"}
```

## Testing

Run auth-specific tests:
```bash
pytest tests/test_auth.py -v
```

Run full suite:
```bash
pytest -q
```

## Production Deployment

1. Set `AUTH_DISABLED=false` (default)
2. Configure JWKS URL for your OAuth provider
3. Set a secure `AUTH_JWT_SECRET` for fallback
4. Consider external rate limiting (Redis) for multi-instance deployments

## Token Requirements

Tokens must include:
- `company_id` claim matching request company_id
- Valid signature (RSA or HMAC)
- Not expired (if `exp` claim present)

Example token payload:
```json
{
  "company_id": "acme_corp",
  "user_id": "user123",
  "exp": 1640995200,
  "iat": 1640991600,
  "iss": "https://auth.example.com"
}
```