"""
Vercel serverless function entry point for AidLinkAI
This file is required for Vercel deployment as it expects the main application
to be in the api/ directory for serverless functions.
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import and run the FastAPI app
from main import app

# Export the app for Vercel
handler = app
