import uvicorn
import os
from main import app  # or wherever your FastAPI app is defined

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))  # Fallback to 8080 if PORT not set
    uvicorn.run("main:app", host="0.0.0.0", port=port)
