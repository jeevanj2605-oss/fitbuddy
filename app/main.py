from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes import router
from app.database import init_db

app = FastAPI(title="FitBuddy API", version="1.0.0")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(router)

@app.on_event("startup")
def startup():
    init_db()
