# main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routers import cards, fortune, advice, retrospective, records

app = FastAPI(title="타로 데이플래너 API")

_raw = os.getenv("ALLOWED_ORIGINS", "")
ALLOWED_ORIGINS = _raw.split(",") if _raw else ["*"]
_credentials = "*" not in ALLOWED_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=_credentials,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.mount("/card_img", StaticFiles(directory="card_img"), name="card_img")

app.include_router(cards.router, prefix="/cards", tags=["cards"])
app.include_router(fortune.router, tags=["fortune"])
app.include_router(advice.router, tags=["advice"])
app.include_router(retrospective.router, tags=["retrospective"])
app.include_router(records.router, prefix="/records", tags=["records"])


@app.get("/health")
def health():
    return {"status": "ok"}
