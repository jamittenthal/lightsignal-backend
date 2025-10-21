"""
CORS preflight tests for backend/main.py

This test suite verifies that CORS configuration correctly:
- Allows localhost origins (http and https on port 3000)
- Allows Vercel preview domains matching the pattern
- Rejects invalid origins
- Properly handles preflight OPTIONS requests
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from main import app

client = TestClient(app)


class TestCORSPreflight:
    """Test CORS preflight (OPTIONS) requests"""

    def test_preflight_localhost_http(self):
        """Test CORS preflight for http://localhost:3000"""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
        assert "POST" in response.headers["access-control-allow-methods"]
        assert "OPTIONS" in response.headers["access-control-allow-methods"]
        assert "Content-Type" in response.headers["access-control-allow-headers"]

    def test_preflight_localhost_https(self):
        """Test CORS preflight for https://localhost:3000"""
        response = client.options(
            "/health",
            headers={
                "Origin": "https://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "https://localhost:3000"
        assert "POST" in response.headers["access-control-allow-methods"]
        assert "OPTIONS" in response.headers["access-control-allow-methods"]
        assert "Authorization" in response.headers["access-control-allow-headers"]

    def test_preflight_vercel_preview_valid(self):
        """Test CORS preflight for valid Vercel preview domain"""
        valid_origins = [
            "https://abc123-lightsignals-projects.vercel.app",
            "https://feature-branch-123-lightsignals-projects.vercel.app",
            "https://pr-42-lightsignals-projects.vercel.app",
            "https://dev-env-lightsignals-projects.vercel.app",
        ]
        
        for origin in valid_origins:
            response = client.options(
                "/api/intent",
                headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type,Authorization",
                },
            )
            assert response.status_code == 200, f"Failed for origin: {origin}"
            assert response.headers["access-control-allow-origin"] == origin, f"Origin header mismatch for: {origin}"
            assert "POST" in response.headers["access-control-allow-methods"]
            assert "OPTIONS" in response.headers["access-control-allow-methods"]

    def test_preflight_vercel_preview_invalid_uppercase(self):
        """Test CORS preflight rejects Vercel domain with uppercase letters"""
        response = client.options(
            "/health",
            headers={
                "Origin": "https://ABC123-lightsignals-projects.vercel.app",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        # FastAPI/Starlette returns 400 for invalid CORS preflight
        assert response.status_code == 400

    def test_preflight_invalid_origin_different_port(self):
        """Test CORS preflight rejects localhost with different port"""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:8000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        # FastAPI/Starlette returns 400 for invalid CORS preflight
        assert response.status_code == 400

    def test_preflight_invalid_origin_wrong_domain(self):
        """Test CORS preflight rejects wrong domain"""
        invalid_origins = [
            "https://malicious-site.com",
            "https://vercel.app",
            "https://lightsignals-projects.vercel.app",  # Missing prefix
            "https://abc-wrong-domain.vercel.app",
            "http://abc123-lightsignals-projects.vercel.app",  # HTTP instead of HTTPS
        ]
        
        for origin in invalid_origins:
            response = client.options(
                "/health",
                headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type",
                },
            )
            # FastAPI/Starlette returns 400 for invalid CORS preflight
            assert response.status_code == 400, f"Should reject origin: {origin}"


class TestCORSActualRequests:
    """Test CORS on actual requests (not just preflight)"""

    def test_get_request_localhost(self):
        """Test GET request with localhost origin"""
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"},
        )
        assert response.status_code == 200
        # GET is not in allowed methods, but endpoint still works
        # CORS headers should not be present for GET since only POST and OPTIONS are allowed
        assert response.json() == {"ok": True}

    def test_post_request_localhost(self):
        """Test POST request with localhost origin"""
        response = client.post(
            "/api/intent",
            headers={
                "Origin": "http://localhost:3000",
                "Content-Type": "application/json",
            },
            json={
                "intent": "dashboard",
                "company_id": "demo",
                "input": {},
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://localhost:3000"

    def test_post_request_vercel_preview(self):
        """Test POST request with Vercel preview domain"""
        response = client.post(
            "/api/intent",
            headers={
                "Origin": "https://test-123-lightsignals-projects.vercel.app",
                "Content-Type": "application/json",
            },
            json={
                "intent": "financial_overview",
                "company_id": "demo",
                "input": {},
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "https://test-123-lightsignals-projects.vercel.app"

    def test_credentials_not_allowed(self):
        """Test that credentials are not allowed (allow_credentials=False)"""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert response.status_code == 200
        # When allow_credentials is False, the header should not be set to "true"
        credentials_header = response.headers.get("access-control-allow-credentials")
        assert credentials_header != "true"
