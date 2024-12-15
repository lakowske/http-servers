"""
FastAPI application with configuration management
"""

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "web.home:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=["./templates", "./templates/web"],
        reload_includes=["*.html"],
    )
