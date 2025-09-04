
from fastapi import FastAPI
from typing import List
import pandas as pd
from pathlib import Path
from .agent_core import LLMClient, review_application

app = FastAPI(title="Loan Review Agent API", version="1.0.0")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
APPS_CSV = DATA_DIR / "loan_applications.csv"
WATCHLIST_CSV = DATA_DIR / "kyc_watchlist.csv"

def _load_watchlist() -> set[str]:
    if WATCHLIST_CSV.exists():
        df = pd.read_csv(WATCHLIST_CSV)
        return set(df["nic"].tolist())
    return set()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/applications")
def list_applications(limit: int = 20):
    df = pd.read_csv(APPS_CSV)
    return df.head(limit).to_dict(orient="records")

@app.get("/review/{application_id}")
def review(application_id: str, model: str = "mistral:latest", use_retrieval: bool = False):
    df = pd.read_csv(APPS_CSV)
    row = df[df["application_id"] == application_id]
    if row.empty:
        return {"error": "application not found"}
    app_row = row.squeeze().to_dict()
    watch = _load_watchlist()
    llm = LLMClient(model=model)
    policy_path = (DATA_DIR.parent / "docs" / "policies" / "policy.md").as_posix()
    result = review_application(app_row, watch, llm, use_retrieval=use_retrieval, policy_path=policy_path)
    return result
