import os
import sys
import uvicorn

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8081"))
    reload = os.environ.get("RELOAD", "false").lower() == "true"
    
    print(f"=== ETSI WPM Unified Suite (v3.0.0) ===")
    print(f"Starting server on http://localhost:{port}")
    print(f"Components: WPM.exe Administration Back-Office + WPM Web Public Portal")
    uvicorn.run("backend.app:app", host=host, port=port, reload=reload)
