import os
os.chdir("/tmp")

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok", "message": "Routing works — dashboard loading next"}

@app.get("/{path:path}")
def catch_all(path: str):
    return {"status": "ok", "path": path}
