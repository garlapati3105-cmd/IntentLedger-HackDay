# IntentLedger

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Tests](https://img.shields.io/badge/tests-67%20passing-2ea44f)](#testing)
[![License](https://img.shields.io/badge/license-not%20specified-lightgrey)](#license)

**IntentLedger is an explainable evaluation workspace for testing whether an AI model preserves a user's final intent across changing multi-turn instructions.**

It compares a simple baseline extraction prompt with an instruction-aware prompt, scores both predictions against human-authored expected states, and shows exactly which fields matched, changed, disappeared, or appeared unexpectedly.

> **Demo scope:** five hand-crafted scenarios. Results are useful for prompt comparison and debugging, but they do not establish general AI reliability.

## Why IntentLedger

Conversational systems often fail when the user's intent changes during a dialogue:

- A corrected value does not fully replace the original.
- An assistant suggestion is mistaken for a user decision.
- A partial update accidentally removes unchanged details.
- A cancellation is represented as an active request.
- An unresolved preference is converted into a confident guess.

IntentLedger turns these failures into inspectable evaluation records instead of hiding them behind a single aggregate score.

## What You Can Do

- Run one scenario or the complete five-case benchmark.
- Compare **Baseline** and **Improved** prompt behavior.
- Inspect the transcript, expected state, predicted state, and raw model output.
- Review field-level `match`, `mismatch`, `missing`, and `unexpected` outcomes.
- Distinguish `PASS`, `FAIL`, and operational `ERROR` results.
- Verify model access separately from API-key presence.
- Preserve evaluation results across normal Streamlit reruns.
- Export existing session results as structured JSON or correctly quoted CSV.
- Use the interface and test suite without making a model call in offline mode.

## Quick Start

### 1. Clone and enter the repository

```bash
git clone https://github.com/garlapati3105-cmd/IntentLedger-HackDay.git
cd IntentLedger-HackDay
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Linux or macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure live evaluation

IntentLedger reads the API key from the `GEMINI_API_KEY` environment variable.

Windows PowerShell:

```powershell
$env:GEMINI_API_KEY = "your-api-key"
```

Linux or macOS:

```bash
export GEMINI_API_KEY="your-api-key"
```

Never commit an API key. `.env` files and `.streamlit/secrets.toml` are excluded by `.gitignore`.

### 5. Launch the application

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501).

## Model Configuration

The default model identifier is:

```text
gemma-4-26b-a4b-it
```

Override it without changing source code:

```powershell
$env:INTENTLEDGER_MODEL = "your-model-id"
```

The sidebar deliberately distinguishes:

- **API key configured** — a non-empty key is present.
- **Live request verified** — the configured model was found through a real model-list request.

Key presence alone is never presented as proof that the model is reachable.

## Two Evaluation Modes

### Baseline

The baseline prompt asks the model to extract the final intended state as JSON. It provides no dedicated rules for conversational corrections or uncertainty.

### Improved

The improved prompt explicitly instructs the model to:

1. Replace earlier values with confirmed corrections.
2. Exclude assistant suggestions rejected by the user.
3. Preserve unchanged fields during partial updates.
4. Represent cancellations as the active final intent.
5. Mark unresolved values as `AMBIGUOUS` and request clarification.

Both modes use the same transcripts, expected states, normalizer, and scorer.

## Benchmark Scenarios

| # | Scenario | What it tests | Required behavior |
|---:|---|---|---|
| 01 | Accepted Correction | Meeting time changes from 2 PM to 3 PM | Keep 3 PM and preserve all unchanged fields |
| 02 | Rejected Suggestion | Assistant proposes La Maison; user rejects it | Retain Bella Italia and exclude the suggestion |
| 03 | Partial Update | Trip budget changes from 2000 to 3000 | Update only the budget |
| 04 | Cancellation | Newsletter signup is later cancelled | Return a cancellation intent and cancelled status |
| 05 | Ambiguous Instruction | User asks for a warm color without choosing one | Mark the color ambiguous and request clarification |

Each JSON case contains a conversation, expected state, clarification requirement, and evaluation note.

## Scoring

Expected fields are compared with the model prediction after normalization.

| Outcome | Meaning | Verdict effect |
|---|---|---|
| `match` | Expected and predicted values are equivalent | Counts toward the match rate |
| `mismatch` | Field exists but contains a different value | Produces `FAIL` |
| `missing` | Expected field is absent | Produces `FAIL` |
| `unexpected` | Prediction contains an extra field | Reported but does not fail by itself |
| `ERROR` | No valid prediction could be scored | Remains operationally distinct from `FAIL` |

Normalization supports:

- Equivalent time formats such as `3pm`, `3:00 PM`, and `15:00`
- Currency and numeric strings such as `$3,000` and `3000`
- Case-insensitive strings
- Order-insensitive lists, including mixed value types

The ambiguous scenario also requires `clarification_needed` to be true.

## Exporting Results

After at least one evaluation, the dashboard enables two downloads:

- **JSON** preserves nested expected and predicted states, field comparisons, verdicts, counts, model ID, format version, and UTC export timestamp.
- **CSV** emits one row per evaluated scenario and prompt mode. Nested states are stored as valid JSON strings inside correctly quoted CSV cells.

Exports include only results already present in Streamlit session state. Downloading does not call the model and missing modes are never fabricated.

ERROR records retain a stable classification such as:

- `offline_mode`
- `quota_exceeded`
- `invalid_api_key`
- `model_not_found`
- `dependency_missing`
- `invalid_response`
- `model_call_failed`

Credential-shaped values and the credential environment-variable name are removed from exported diagnostics.

## Architecture

```text
Conversation case
      |
      v
engine/prompts.py        Build baseline or improved prompt
      |
      v
engine/extractor.py      Call the configured model and parse an object
      |
      v
engine/normalizer.py     Canonicalize comparable values
      |
      v
engine/scorer.py         Produce field results and PASS/FAIL/ERROR
      |                              |
      v                              v
app.py + ui.py            engine/exporter.py
Interactive dashboard     JSON and CSV serialization
```

### Project Structure

```text
IntentLedger-HackDay/
├── app.py                         Streamlit application and session state
├── ui.py                          Reusable UI renderers and design system
├── requirements.txt
├── engine/
│   ├── extractor.py               Model access, parsing, and error handling
│   ├── exporter.py                JSON/CSV serialization and sanitization
│   ├── loader.py                  Benchmark loader
│   ├── normalizer.py              Canonical value normalization
│   ├── prompts.py                 Baseline and improved prompts
│   └── scorer.py                  Field-level scoring and summaries
├── tests/
│   ├── cases/                     Five benchmark scenarios
│   ├── test_exporter.py
│   ├── test_extractor_config.py
│   ├── test_normalizer.py
│   └── test_scorer.py
└── tools/
    └── build_project_report.py     Optional Word report generator
```

## Offline Mode

When `GEMINI_API_KEY` is absent or empty:

- No model request is made.
- Evaluations return `ERROR` with the offline classification.
- The transcript, expected state, navigation, export controls, and ERROR views remain testable.
- Offline results are never displayed as model scores.

This makes the evaluation harness safe to inspect and demonstrate without credentials.

## Testing

Run the complete suite:

```bash
pytest tests -v
```

Current status: **67 tests passing**.

Coverage includes:

- Default and overridden model configuration
- API-key presence and offline behavior
- Plain, fenced, embedded, malformed, and wrong-shape JSON output
- Time, currency, number, string, and list normalization
- PASS, FAIL, ERROR, clarification, and aggregate scoring paths
- Successful, partial-mode, empty, and ERROR exports
- Nested JSON preservation and CSV quoting
- Unicode, commas, quotation marks, and newlines in exported fields
- Credential redaction and prevention of fabricated results

Tests do not require a live API key.

## Common Commands

```bash
# Launch the app
streamlit run app.py

# Run all tests
pytest tests -v

# Run only exporter tests
pytest tests/test_exporter.py -v

# Override the model for one PowerShell session
$env:INTENTLEDGER_MODEL = "your-model-id"
```

## Limitations

1. The benchmark contains five hand-crafted English scenarios.
2. It evaluates one configured model at a time.
3. Prompt wording can affect results.
4. The model must return a JSON object; strict schema-based structured output is not enabled.
5. Cases are short and do not represent long-context or adversarial conversations.
6. Live results depend on external API availability, quota, credentials, and model access.

## Roadmap

- Expand the benchmark with independently reviewed scenarios.
- Add repeated-run and multi-model comparison.
- Export latency and token-usage metadata when available.
- Add strict structured-output schemas.
- Add longer, multilingual, and adversarial conversations.
- Add CI checks for tests and Streamlit startup.

## Responsible Use

IntentLedger is an evaluation aid, not a certification system. A PASS means that one model response matched one expected state under the current normalizer and prompt. It does not prove that the model is safe, reliable, or suitable for high-stakes deployment.

## AI Assistance Disclosure

This hackathon project was developed with AI coding assistance under human supervision. The runtime evaluation model is configured separately through the Google Gen AI SDK. Benchmark cases and expected states should be reviewed by a human before results are used for decision-making.

## License

No open-source license has been added yet. Until a license is provided, standard copyright restrictions apply.

---

Built with Python, Streamlit, and the Google Gen AI SDK.
