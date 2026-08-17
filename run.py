import os
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main_v2:app",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8765")),
        reload=os.getenv("RELOAD", "0") == "1",
    )
