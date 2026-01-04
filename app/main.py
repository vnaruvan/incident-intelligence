from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from sqlalchemy import text
from app.core.database import SessionLocal
from sqlalchemy import text
from app.core.database import engine

from app.api.routes import router as api_router

STATIC_DIR = Path(__file__).resolve().parent / "static"


def create_app() -> FastAPI:
    app = FastAPI(
        title="Incident Intelligence API",
        docs_url=None,
        redoc_url=None,
        openapi_url="/openapi.json",
    )

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/health", include_in_schema=False)
    def health():
        # Liveness: process is up
        return {"status": "ok"}

    @app.get("/ready", include_in_schema=False)
    def ready():
        # Readiness: DB reachable
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return {"status": "ready"}
        except Exception as e:
            raise HTTPException(status_code=503, detail="db not ready") from e

    @app.get("/", include_in_schema=False)
    def root():
        html = """
        <html>
          <head><title>Incident Intelligence</title></head>
          <body style="font-family: system-ui; padding: 24px;">
            <h2>Incident Intelligence</h2>
            <ul>
              <li><a href="/ui">Demo Console</a></li>
              <li><a href="/docs">Swagger Docs</a></li>
              <li><a href="/redoc">ReDoc</a></li>
            </ul>
          </body>
        </html>
        """
        return HTMLResponse(html)

    @app.get("/docs", include_in_schema=False)
    def custom_docs():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title="Incident Intelligence API Docs",
            swagger_css_url="/static/docs.css",
            swagger_ui_parameters={
                "docExpansion": "none",
                "defaultModelsExpandDepth": -1,
                "displayRequestDuration": True,
                "tryItOutEnabled": True,
            },
        )

    @app.get("/redoc", include_in_schema=False)
    def redoc():
        return get_redoc_html(
            openapi_url=app.openapi_url,
            title="Incident Intelligence API ReDoc",
        )

    @app.get("/ui", include_in_schema=False)
    def ui():
        return HTMLResponse((STATIC_DIR / "console.html").read_text(encoding="utf-8"))

    app.include_router(api_router, prefix="/api")
    return app


app = create_app()
