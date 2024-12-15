"""
FastAPI application with configuration management
"""

from fastapi import WebSocket, Request

from web.homepage import app
from fastapi.templating import Jinja2Templates

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def index(request: Request):
    """
    Index page
    """
    return templates.TemplateResponse("web/homepage.html", {"request": request})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "web.homepage:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=["./templates", "./templates/web"],
        reload_includes=["*.html"],
    )
