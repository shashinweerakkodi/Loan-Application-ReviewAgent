
# Loan Application Review Agent (Ollama)

A single-agent system that reviews synthetic loan applications, runs KYC/AML and policy checks, and produces **Approve / Reject / Flag** recommendations with explanations. Designed to run **fully locally** using [Ollama](https://ollama.com/) and open models (e.g., `mistral:latest`).

## Features
- Synthetic data: 30 applications + KYC watchlist
- Policy checks: KYC, AML, Watchlist, Credit Score, DTI, Delinquency, Affordability
- Risk scoring (0.0–1.0) and transparent reasons
- **Ollama LLM** for human-friendly explanation (with safe fallback)
- REST API (FastAPI) and **Streamlit UI**

## Setup

1. Install Python 3.10+ and dependencies:
   ```bash
   pip install fastapi uvicorn streamlit pydantic pandas
   ```

2. Install Ollama and pull a model (optional but recommended):
   ```bash
   # Install Ollama from https://ollama.com/
   ollama pull mistral:latest
   ```

## Run API

```bash
cd app
uvicorn app.api:app --reload
# API docs at: http://localhost:8000/docs
```

## Run UI (Streamlit)

```bash
cd app
streamlit run streamlit_app.py
```

## Project Structure

```
loan_agent/
├─ app/
│  ├─ agent_core.py       # core checks, risk scoring, Ollama client
│  ├─ api.py              # FastAPI app exposing endpoints
│  ├─ schemas.py          # Pydantic models
│  └─ streamlit_app.py    # Streamlit UI
├─ data/
│  ├─ loan_applications.csv
│  └─ kyc_watchlist.csv
├─ tests/
│  └─ test_agent.py
└─ README.md
```

## How it works
1. Loads an application record and the KYC watchlist.
2. Runs policy checks and computes a **risk score**.
3. Chooses **APPROVE/FLAG/REJECT**.
4. Calls **Ollama** to generate a concise explanation (or uses fallback).
5. Returns a JSON decision and explanation.



## How the LLM Works

The agent is **rules-first** and uses the LLM **only for explanations**:

1. **Deterministic checks** compute signals: `KYC`, `AML`, `Watchlist`, `CreditScore`, `DTI`, `Delinquency`, `Affordability`.
2. A **weighted risk score (0–1)** is calculated; then a **policy decision** is made:
   - Any FAIL on **KYC/AML/Watchlist** ⇒ **REJECT**
   - Else if ≥2 WARN ⇒ **FLAG**
   - Else ⇒ **APPROVE**
3. The agent prepares a **prompt** with (a) key application facts and (b) the policy reasons, then asks the LLM to produce a clear, business-friendly summary.
4. If Ollama is not available, a **deterministic fallback** explanation is used so the system is still usable.

### Prompt Shape (example)

```text
You are a senior credit analyst. Summarize the decision for a loan application in 120 words.

Application facts (JSON):
{facts_json}

Policy reasons (list):
{reasons_list}

Final recommendation: {action}
Explain in clear, business-friendly language with numbered points and a brief closing sentence.
```

> You can customize the wording by editing **`prompt_template.txt`** (see below).

### Why this design?
- **Transparent**: Business rules never depend on the LLM.
- **Explainable**: Human-readable justifications for loan officers and auditors.
- **Modular**: Swap models (`mistral`, `llama3`, `gemma`) without changing the policy engine.



## Quick Start (UI)

1. **Unzip** the project and open a terminal in the folder.
2. Install deps:
   ```bash
   pip install fastapi uvicorn streamlit pydantic pandas
   ```
3. (Optional) Install **Ollama** and pull a model:
   ```bash
   # https://ollama.com/ — then:
   ollama pull mistral:latest
   ```
4. Run the UI:
   ```bash
   cd app
   streamlit run streamlit_app.py
   ```
5. In the browser: select an `application_id` → click **Run Review**.
   - Toggle **“Use policy retrieval (RAG)”** to inject policy excerpts into the LLM prompt.



## Vector Databases & RAG (in this project)

**Vector databases** store texts as **embeddings** (numeric vectors) so you can do **semantic search**. This is useful to fetch the *right* policy paragraphs for the LLM to cite.  
This project includes a **lightweight retrieval module** that works out-of-the-box (no extra installs). It does simple semantic-ish search locally. If you want a true vector DB:

- Install **ChromaDB** and a sentence-transformer model:
  ```bash
  pip install chromadb sentence-transformers
  ```
- Replace the simple search in `app/retrieval.py` with a Chroma-backed search (instructions inside the file).
- The UI already has “Use policy retrieval (RAG)”; retrieved passages are appended to the LLM prompt.

**Status**: Retrieval is **included** (simple mode). Vector DB is **optional** and not required to run.
