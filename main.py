"""
FastAPI application with configuration management
"""

from fastapi import Request
from fastapi.templating import Jinja2Templates
from web.homepage import app
from actions.build import list_functions


# Initialize Jinja2 templates
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def index(request: Request):
    """
    Index page
    """
    functions = list_functions()
    return templates.TemplateResponse(
        "web/homepage.html", {"request": request, "functions": functions}
    )


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
