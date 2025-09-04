
from app.agent_core import run_policy_checks, score_risk, decide

def test_risk_score_monotonic():
    checks_low = {"KYC":"PASS","AML":"PASS","Watchlist":"PASS","CreditScore":"PASS","DTI":"PASS","Delinquency":"PASS","Affordability":"PASS"}
    checks_mid = {"KYC":"PASS","AML":"PASS","Watchlist":"PASS","CreditScore":"WARN","DTI":"WARN","Delinquency":"PASS","Affordability":"PASS"}
    checks_high = {"KYC":"FAIL","AML":"PASS","Watchlist":"PASS","CreditScore":"WARN","DTI":"WARN","Delinquency":"PASS","Affordability":"WARN"}
    assert score_risk(checks_low) < score_risk(checks_mid) <= score_risk(checks_high)

def test_decide_fail_is_reject():
    checks = {"KYC":"FAIL","AML":"PASS","Watchlist":"PASS","CreditScore":"PASS","DTI":"PASS","Delinquency":"PASS","Affordability":"PASS"}
    assert decide(checks) == "REJECT"
