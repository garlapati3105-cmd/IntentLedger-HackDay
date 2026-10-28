# IntentLedger

> **A developer tool that evaluates whether an AI system correctly tracks changing instructions across multi-turn conversations.**

⚠️ **Small demonstration benchmark (5 hand-crafted cases). Results do NOT establish general AI reliability.**

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [API Configuration](#api-configuration)
5. [Running the Application](#running-the-application)
6. [Running the Tests](#running-the-tests)
7. [Test Cases](#test-cases)
8. [Evaluation Modes](#evaluation-modes)
9. [Offline Mode](#offline-mode)
10. [Limitations](#limitations)
11. [AI-Tool Disclosure](#ai-tool-disclosure)

---

## Overview

AI assistants often fail to correctly track user intent when instructions change mid-conversation: the user corrects a value, rejects a suggestion, partially updates a request, cancels an action, or leaves an instruction ambiguous.

**IntentLedger** runs structured conversation test cases through a model, extracts a JSON representation of the "final intended state," and compares it field-by-field against a human-authored ground truth.

### Key features

| Feature | Description |
|---|---|
| **5 scenario types** | Correction, rejection, partial update, cancellation, ambiguity |
| **Two evaluation modes** | Baseline (naive prompt) vs Improved (instruction-tracking prompt) |
| **Field-level scoring** | Match / mismatch / missing / unexpected per field |
| **Clarification metric** | Separate metric for the ambiguous case |
| **Normalization** | Time strings, currency, lists compared canonically |
| **Offline mode** | Validate harness and UI without an API key |
| **PASS / FAIL / ERROR** | Clear verdict per run |
| **JSON and CSV export** | Download only the evaluation records currently stored in session |

---

## Architecture

```
IntentLedger-HackDay/
├── app.py                     # Streamlit UI
├── requirements.txt
├── engine/
│   ├── __init__.py
│   ├── extractor.py           # Google Gen AI model calls & offline mode
│   ├── normalizer.py          # Value normalisation (time, currency, lists)
│   ├── prompts.py             # Baseline & improved system prompts
│   ├── scorer.py              # Field-level comparison & scoring
│   ├── exporter.py            # JSON/CSV report serialization and sanitization
│   └── loader.py              # Test-case loader
└── tests/
    ├── __init__.py
    ├── test_scorer.py         # Unit tests for scorer
    ├── test_normalizer.py     # Unit tests for normalizer
    └── cases/
        ├── 01_accepted_correction.json
        ├── 02_rejected_suggestion.json
        ├── 03_partial_update.json
        ├── 04_cancellation.json
        └── 05_ambiguous_instruction.json
```

### Data flow

```
Conversation transcript
        │
        ▼
  engine/prompts.py   ──►  build_extraction_prompt(mode)
        │
        ▼
  engine/extractor.py ──►  Google Gen AI API  ──►  raw JSON string
        │
        ▼
  engine/normalizer.py ──► normalize each field value
        │
        ▼
  engine/scorer.py    ──►  field-level ScoreResult (PASS/FAIL/ERROR)
        │
        ▼
       app.py         ──►  Streamlit UI display
```

---

## Installation

```bash
cd IntentLedger-HackDay
pip install -r requirements.txt
```

Python 3.11+ recommended.

---

## API Configuration

IntentLedger uses the **Google Gen AI Python SDK** (`google-genai`) and by default calls
**Google's hosted Gemma 4 model** (`gemma-4-26b-a4b-it`) through the Gemini API.
The model runs on Google's infrastructure — it is not a local deployment.

### Set your API key

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY = "your-api-key-here"
```

**Linux / macOS:**
```bash
export GEMINI_API_KEY="your-api-key-here"
```

**Streamlit secrets (`.streamlit/secrets.toml`):**
```toml
GEMINI_API_KEY = "your-api-key-here"
```

> ⚠️ Never hardcode API keys in source files. The key is read exclusively from the environment variable `GEMINI_API_KEY`.

### Configure the model (optional)

The default model is `gemma-4-26b-a4b-it` (hosted Gemma 4 via the Gemini API). Override with:

```powershell
$env:INTENTLEDGER_MODEL = "gemini-2.0-flash"
```

The application will verify that the selected model is available via the Gen AI API and show an error if it is not.

---

## Running the Application

```bash
streamlit run app.py
```

Then open [http://localhost:8501](http://localhost:8501) in your browser.

### Controls

- **Scenario selector** (sidebar) — pick a test case to inspect
- **▶ Run Baseline / ▶ Run Improved** — run the selected case in one mode
- **▶ Run All — Baseline / ▶ Run All — Improved** — run all 5 cases
- **Compare tab** — side-by-side baseline vs improved for the selected case
- **All Cases table** (bottom) — overview of every verdict and match rate
- **Download JSON / Download CSV** — export existing session results without running the model again

---

## Running the Tests

```bash
pytest tests/ -v
```

The tests cover:
- Scorer: exact match, mismatch, missing field, unexpected field, ERROR path
- Scorer: time normalisation (3pm == 3:00 PM), currency ($3,000 == 3000)
- Scorer: clarification metric (ambiguous case)
- Scorer: aggregate summary (`summarise`)
- Normalizer: time strings, 24h format, noon/midnight edge cases
- Normalizer: currency stripping, int/float equality
- Normalizer: list sorting, string case/whitespace

No API key is required to run the tests — they use only the scoring and normalisation logic.

---

## Test Cases

| # | Name | Scenario Type | Key challenge |
|---|---|---|---|
| 01 | Accepted Correction | `accepted_correction` | 2 PM → 3 PM: old value must be discarded |
| 02 | Rejected Suggestion | `rejected_suggestion` | La Maison proposed but rejected; Bella Italia must win |
| 03 | Partial Update | `partial_update` | Budget $2k → $3k; destination/duration/accommodation unchanged |
| 04 | Cancellation | `cancellation` | Subscription active → must become cancelled |
| 05 | Ambiguous Instruction | `ambiguous_instruction` | Colour "something warm" — model must flag uncertainty |

Each case contains:
- `conversation` — the multi-turn transcript
- `expected_state` — human-authored ground truth JSON
- `clarification_expected` — whether the ambiguity metric applies
- `notes` — explanation of what the model must get right

---

## Evaluation Modes

### Baseline

A simple prompt: *"Extract the final intended state as JSON."*

No special instructions about corrections, rejections, or ambiguity.

### Improved

An explicit prompt that instructs the model to:
1. **Corrections** — use only the most recent value
2. **Rejected suggestions** — exclude anything the user rejected
3. **Partial updates** — retain unchanged fields
4. **Cancellations** — set action to the cancellation intent and status to `"cancelled"`
5. **Ambiguity** — set ambiguous fields to `"AMBIGUOUS"` and add `clarification_needed: true`

Both modes are run on the **same cases and expected states**. Scores are never fabricated; they come from actual model responses.

---

## Offline Mode

When `GEMINI_API_KEY` is not set (or set to an empty string), IntentLedger enters **offline mode**:

- No model calls are made.
- Every case returns an `ERROR` result with the label **"OFFLINE MODE"**.
- You can still validate the UI, test-case display, field table, and tab layout.
- The offline state is prominently displayed in the sidebar and result panels.
- Offline results are never labelled as real model results.

---

## Limitations

1. **5 cases only.** This is a demonstration benchmark, not a statistically valid evaluation.
2. **Single model.** We test one model at a time. Different model families may behave differently.
3. **Prompt sensitivity.** Small prompt wording changes can shift verdicts. The improved prompt was written by hand and may not generalise.
4. **JSON-only extraction.** The model must output valid JSON. Structured output mode is not used, so parsing failures are possible.
5. **No multi-hop reasoning.** Cases have at most 4 turns. Longer conversations may reveal different failure modes.
6. **English only.** Cases are in English; no multilingual evaluation.

---

## AI-Tool Disclosure

This project was built with **AI coding assistance** as part of a hackathon:

| Tool | Use |
|---|---|
| **Antigravity (Google Deepmind)** | Full implementation: file creation, engine modules, Streamlit UI, unit tests, README |
| **Google Gemma 4 (hosted via google-genai SDK)** | Default runtime model (`gemma-4-26b-a4b-it`) for intent extraction — runs on Google infrastructure, not locally |

All test cases and expected states were authored and reviewed by the human developer. The AI assistant wrote code under human supervision.

---

*IntentLedger · HackDay 2026 · Built with Python, Streamlit, and Google Gen AI*
