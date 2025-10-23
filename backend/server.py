# /app/backend/server.py
"""
Entry point for supervisor - routes to /app/app/main.py
This ensures the canonical FastAPI app at /app/app/main.py is used.
"""
import sys
from pathlib import Path

# Add parent directory to path so we can import from app/
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the canonical app from /app/app/main.py
from app.main import app

# Optional: Log that we're using the canonical app
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("✓ Backend server routing to canonical FastAPI app at /app/app/main.py")
logger.info("✓ Demo mode available: use company_id='demo' for all endpoints")
logger.info("✓ DEV_NONDEMO_STUB env toggle available for development")

# Expose app for uvicorn
__all__ = ["app"]
