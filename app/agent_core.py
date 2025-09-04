"""
Agent core logic. Uses Ollama locally if available; otherwise falls back to a deterministic explainer.
"""
from __future__ import annotations
from typing import List, Dict, Any
from pathlib import Path
import requests


# Ollama client (TinyLlama by default)
class LLMClient:
    def __init__(self, model: str = "tinyllama"):
        self.model = model
        self._prompt_tmpl = None
        self.base_url = "http://localhost:11434/api/generate"

        # Load optional external prompt template
        try:
            tmpl_path = Path(__file__).resolve().parents[1] / "prompt_template.txt"
            if tmpl_path.exists():
                self._prompt_tmpl = tmpl_path.read_text()
        except Exception:
            self._prompt_tmpl = None

    def explain(
        self,
        facts: Dict[str, Any],
        reasons: List[str],
        action: str,
        policy_snippets: List[Dict[str, str]] | None = None,
    ) -> str:
        """
        Uses Ollama to craft a human-readable rationale. Falls back to template if Ollama unavailable.
        """

        # Build prompt from template if available
        if self._prompt_tmpl:
            citations = "\n".join(
                [f"- {s.get('title','')}: {s.get('text','')[:200]}" for s in (policy_snippets or [])]
            )
            prompt = self._prompt_tmpl.format(
                facts=facts,
                reasons="\n".join(reasons),
                action=action,
            ).strip()
            if citations:
                prompt += f"\n\nRelevant policy excerpts:\n{citations}"
        else:
            prompt = f"""You are a senior credit analyst. Summarize the decision for a loan application in 120 words.

Application facts (JSON):
{facts}

Policy reasons (list):
{reasons}

Final recommendation: {action}
Explain in clear, business-friendly language with numbered points and a brief closing sentence."""

        # Call Ollama API
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
            response = requests.post(self.base_url, json=payload, timeout=60)
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except Exception:
            return self._fallback(facts, reasons, action, policy_snippets)

    def _fallback(
        self,
        facts: Dict[str, Any],
        reasons: List[str],
        action: str,
        policy_snippets: List[Dict[str, str]] | None = None,
    ) -> str:
        bullets = "".join([f"\n  - {r}" for r in reasons])
        cites = "".join(
            [f"\n  * Policy cite: {s.get('title','')}" for s in (policy_snippets or [])]
        )
        return f"Decision: {action}. Key reasons:{bullets}{cites}\nSummary: Based on policy checks and risk signals, the recommended action is {action}."


def run_policy_checks(app: Dict[str, Any], watchlist_set: set[str]) -> Dict[str, str]:
    checks = {}
    # Critical blocks
    checks["KYC"] = "FAIL" if app["kyc_status"] != "Verified" else "PASS"
    checks["AML"] = "FAIL" if app["aml_flag"] else "PASS"
    checks["Watchlist"] = "FAIL" if app["nic"] in watchlist_set else "PASS"
    # Financial risk
    checks["CreditScore"] = "WARN" if app["credit_score"] < 600 else "PASS"
    checks["DTI"] = "WARN" if app["dti"] > 0.45 else "PASS"
    checks["Delinquency"] = "WARN" if app["delinquency_12m"] >= 2 else "PASS"
    # Affordability (very simple heuristic)
    affordable = app["requested_amount_lkr"] <= app["monthly_income_lkr"] * 20
    checks["Affordability"] = "WARN" if not affordable else "PASS"
    return checks


def score_risk(checks: Dict[str, str]) -> float:
    weights = {
        "KYC": 0.25,
        "AML": 0.25,
        "Watchlist": 0.2,
        "CreditScore": 0.12,
        "DTI": 0.1,
        "Delinquency": 0.04,
        "Affordability": 0.04,
    }
    s = 0.0
    for k, v in checks.items():
        if v == "FAIL":
            s += weights.get(k, 0)
        elif v == "WARN":
            s += weights.get(k, 0) * 0.5
    return min(1.0, round(s, 3))


def decide(checks: Dict[str, str]) -> str:
    if any(checks[c] == "FAIL" for c in ["KYC", "AML", "Watchlist"]):
        return "REJECT"
    warns = sum(1 for v in checks.values() if v == "WARN")
    return "FLAG" if warns >= 2 else "APPROVE"


def reasons_from_checks(app: Dict[str, Any], checks: Dict[str, str]) -> List[str]:
    r = []
    if checks["KYC"] == "FAIL":
        r.append(f"KYC status is {app['kyc_status']}.")
    if checks["AML"] == "FAIL":
        r.append("Positive AML risk signal detected.")
    if checks["Watchlist"] == "FAIL":
        r.append("Applicant NIC matched internal/external watchlist.")
    if checks["CreditScore"] == "WARN":
        r.append(f"Low credit score: {app['credit_score']}.")
    if checks["DTI"] == "WARN":
        r.append(f"High DTI ratio: {app['dti']}.")
    if checks["Delinquency"] == "WARN":
        r.append(f"Delinquencies in last 12 months: {app['delinquency_12m']}.")
    if checks["Affordability"] == "WARN":
        r.append("Requested amount is high vs income (affordability concern).")
    if not r:
        r.append("All core checks passed within policy thresholds.")
    return r


def review_application(
    app: Dict[str, Any],
    watchlist_set: set[str],
    llm: LLMClient,
    use_retrieval: bool = False,
    policy_path: str | None = None,
) -> Dict[str, Any]:
    checks = run_policy_checks(app, watchlist_set)
    risk = score_risk(checks)
    action = decide(checks)
    reasons = reasons_from_checks(app, checks)

    # (Optional) retrieve relevant policy snippets
    policy_snippets = []
    if use_retrieval and policy_path:
        try:
            from .retrieval import search_policy
            query = " ".join(reasons)
            policy_snippets = search_policy(query, Path(policy_path), top_k=3)
        except Exception:
            policy_snippets = []

    explanation = llm.explain(
        facts={
            k: v
            for k, v in app.items()
            if k
            in [
                "application_id",
                "full_name",
                "age",
                "employment_status",
                "monthly_income_lkr",
                "requested_amount_lkr",
                "credit_score",
                "dti",
                "delinquency_12m",
                "loan_purpose",
            ]
        },
        reasons=reasons,
        action=action,
        policy_snippets=policy_snippets,
    )

    return {
        "application_id": app["application_id"],
        "recommended_action": action,
        "reasons": reasons,
        "risk_score": risk,
        "checks": checks,
        "explanation": explanation,
    }
