# Symptom Pattern Notebook

A Streamlit prototype that helps someone recognise possible PCOS-related
symptom patterns from their own free-text narrative — without diagnosing
them. Built from a project brief for an HCAI (human-centred AI) evaluation
study.

## What it does

Someone describes their symptoms in their own words. Claude identifies
which of four symptom clusters (Ovulation, Metabolic, Androgenic,
Psychological) their narrative touches on, explains the reasoning in
plain, non-diagnostic language, and suggests questions they could bring to
a doctor. The relevant phrases in their own narrative are highlighted to
show exactly what informed each pattern.

**This is not a diagnostic tool.** It always recommends discussing
patterns with a healthcare professional.

## Running it locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your ANTHROPIC_API_KEY, or leave blank for mock mode
streamlit run app.py
```

Runs at `http://localhost:8501`. With no API key set, it runs in **mock
mode** — a simple keyword matcher stands in for Claude, so you can try the
whole app for free.

## Running the tests

```bash
python3 -m pytest tests/ -v
```

## Project structure

```
app.py                  Streamlit UI, submission handling, results display
prompts.py               Builds Claude's instructions from data/clusters.json
llm_client.py             Calls Claude, with retries and a mock mode fallback
validation.py             Checks narrative length/content before submitting
data/clusters.json        The four symptom clusters and their term lists
tests/                    Automated tests (validation, LLM output, highlighting)
```
