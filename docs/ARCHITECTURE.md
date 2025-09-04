
# Architecture & Flow

```mermaid
flowchart LR
    A[Loan Application Record] --> B[Policy Checks\nKYC / AML / Watchlist / Score / DTI / Delinquency / Affordability]
    B --> C[Risk Score (0–1)]
    C --> D{Decision}
    D -->|APPROVE / FLAG / REJECT| E[Decision JSON]
    B --> F[Reasons List]
    E --> G[LLM Prompt Builder]
    F --> G
    G --> H[Ollama LLM (e.g., mistral:latest)]
    H --> I[Human-friendly Explanation]
    E --> J[API / UI Response]
    I --> J
```

- **Rules-first** engine guarantees consistent decisions.
- **LLM** adds business-facing explanation only.
- Works offline (fallback) and upgrades easily to local LLMs via **Ollama**.
