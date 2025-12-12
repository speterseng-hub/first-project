# main.py
from dotenv import load_dotenv

load_dotenv()
from fastapi import FastAPI
from app.router import router
import os


app = FastAPI(title="Stock Analytics GCP")

app.include_router(router)
print("DEBUG PROJECT_ID =", os.getenv("PROJECT_ID"))

@app.get("/healthz")
def health():
    return {"status": "ok", "project": os.environ.get("PROJECT_ID")}
