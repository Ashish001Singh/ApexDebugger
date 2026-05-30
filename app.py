from fastapi import FastAPI
from pydantic import BaseModel

from src.apex_copilot.review import review

app = FastAPI(title="ApexDebugger", version="0.1.0")


class ReviewRequest(BaseModel):
    code: str
    filename: str = "anonymous.cls"


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/review")
def review_endpoint(req: ReviewRequest) -> dict:
    result = review(req.code, filename=req.filename)
    return result.model_dump()
