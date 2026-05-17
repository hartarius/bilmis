"""
BİLMİŞ — Vercel Python Serverless Function Entry Point
"""

import os
import sys

# Add backend directory to Python path
backend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend")
sys.path.insert(0, backend_dir)

from main import app  # noqa: E402

# Vercel uses this ASGI app as the handler
# All API routes are served through this single FastAPI app
