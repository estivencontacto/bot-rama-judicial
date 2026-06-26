import uvicorn

from backend.app.core.settings import get_settings


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8010 if settings.environment == "local" else 8000,
        reload=settings.debug,
    )
