#!/usr/bin/env python3
"""
Simple script to run the OpenHands Runner service locally
"""
import os
import sys
import uvicorn
from app.config import settings

def main():
    """Run the application"""
    # Set default environment variables if not set
    if not os.getenv("DATABASE_URL"):
        print("Warning: DATABASE_URL not set. Using SQLite for development.")
        os.environ["DATABASE_URL"] = "sqlite:///./runner.db"
    
    # Run the server
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        reload=True if os.getenv("ENV") == "development" else False,
        log_level=settings.log_level.lower()
    )

if __name__ == "__main__":
    main()