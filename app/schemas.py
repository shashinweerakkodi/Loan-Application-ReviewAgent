
from pydantic import BaseModel, Field, conint, confloat
from typing import Optional, Literal, List, Dict

class LoanApplication(BaseModel):
    application_id: str
    full_name: str
    nic: str
    age: conint(ge=18, le=75)
    employment_status: Literal["Salaried", "Self-Employed", "Unemployed", "Contract"]
    monthly_income_lkr: conint(ge=0)
    existing_debt_lkr: conint(ge=0)
    requested_amount_lkr: conint(ge=0)
    loan_purpose: str
    credit_score: conint(ge=300, le=900)
    kyc_status: Literal["Verified", "Pending", "Rejected"]
    aml_flag: bool
    delinquency_12m: conint(ge=0)
    dti: confloat(ge=0, le=1)

class Decision(BaseModel):
    application_id: str
    recommended_action: Literal["APPROVE", "REJECT", "FLAG"]
    reasons: List[str]
    risk_score: confloat(ge=0, le=1) = 0.0
    checks: Dict[str, str] = Field(default_factory=dict)
