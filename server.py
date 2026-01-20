import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Impserver main app from app folder
try:
    from app.main import app as main_app

    # Add CORS middleware
    main_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app = main_app

except ImportError as e:
    print(f"Import Error: {e}")
    # Fallback: Create simple FastAPI app
    app = FastAPI(title="RAG Chatbot API")

    @app.get("/")
    def root():
        return {"error": "Main app not found", "details": str(e)}


# Health check endpoint
@app.get("/health")
def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
