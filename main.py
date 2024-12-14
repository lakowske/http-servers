"""
FastAPI application with configuration management
"""

from fastapi import WebSocket, Request
from web.homepage import app
from fastapi.templating import Jinja2Templates

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="templates")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for retrieving and updating configuration
    """
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")


@app.get("/")
async def index(request: Request):
    """
    Index page
    """
    return templates.TemplateResponse("homepage.html", {"request": request})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("web.homepage:app", host="127.0.0.1", port=8000, reload=True)
