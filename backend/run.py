"""Application entrypoint for running IP-SAKTI Backend server."""
import os
import uvicorn
from app.config import settings

if __name__ == "__main__":
    port = int(os.getenv("PORT", str(settings.PORT)))
    host = os.getenv("HOST", settings.HOST)
    print(f"Starting IP-SAKTI server on {host}:{port} ...")
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=settings.DEBUG,
        log_level="info"
    )
