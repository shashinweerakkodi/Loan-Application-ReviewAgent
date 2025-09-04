
# LLM Integration (Deep Dive)

## Responsibilities
- Generate a concise, professional **explanation** of an already-made decision.
- Do **not** alter the outcome; policy checks define the decision.

## Inputs to the prompt
- **Facts**: id, name, age, employment, income, requested amount, credit score, DTI, delinquencies, purpose.
- **Reasons**: messages derived from WARN/FAIL checks.
- **Action**: APPROVE / FLAG / REJECT.

## Output
- 100–150 word summary with numbered points and a brief closing line.

## Customizing the Prompt
Edit `prompt_template.txt` at the project root. Variables available:
- `{facts}` – Python dict of selected facts
- `{reasons}` – list of reason strings
- `{action}` – final recommendation string

If the file is missing, the agent uses a built-in default.
