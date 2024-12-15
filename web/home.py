"""
Home page and WebSocket endpoint for enabling actions on the web
"""

import logging
from contextlib import asynccontextmanager
from fastapi.websockets import WebSocketState, WebSocketDisconnect, WebSocket
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from configuration.container import ServerContainer
from actions.build import list_functions

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="templates")

container = ServerContainer()
app = container.app_provider().get_app()
connected_websockets = set()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI, websockets: set = connected_websockets):
    """
    Context manager to handle the lifespan of the FastAPI application.
    """
    print("We starting up")
    yield
    print("Shutting down websockets")
    for websocket in connected_websockets:
        print("Attempting to close websocket %s" % str(websocket.client))
        if not websocket.client_state.name != WebSocketState.DISCONNECTED:
            await websocket.close()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for retrieving and updating configuration.
    """
    await websocket.accept()
    connected_websockets.add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect as e:
        logger.info("Got a disconnect exception: %s", e)
        return
    except RuntimeError as e:
        logger.error("Error processing websocket: %s", e)
        connected_websockets.remove(websocket)
        if not websocket.client_state != WebSocketState.DISCONNECTED:
            try:
                await websocket.close()
            except RuntimeError as e:
                logger.error("Error closing websocket: %s", e)


@app.get("/")
async def index(request: Request):
    """
    Index page
    """
    functions = list_functions()
    return templates.TemplateResponse(
        "web/homepage.html", {"request": request, "functions": functions}
    )
