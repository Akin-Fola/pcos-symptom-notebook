import json
import logging
import os
import time

from prompts import build_system_prompt, CLUSTER_NAMES

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger("pcos_prototype.llm_client")

MODEL_NAME = "claude-sonnet-4-5"
MAX_TOKENS = 1024
MAX_RETRIES = 2


class LLMError(Exception):
    """Raised when the LLM call fails after retries, or returns unusable output."""
    pass

def _get_api_key() -> str | None:
    try:
        import streamlit as st
        if "ANTHROPIC_API_KEY" in st.secrets:
            return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        pass
    return os.environ.get("ANTHROPIC_API_KEY")

def _mock_response(narrative_text: str) -> dict:
    """
    Deterministic keyword-based mock, used only when no API key is configured.
    Lets the whole app run and be tested without live API access. NOT the
    real pattern-recognition logic — just a stand-in for development.
    """
    text_lower = narrative_text.lower()
    keyword_map = {
        "OVULATION": ["period", "cycle", "amenorrhea", "ovulat"],
        "METABOLIC": ["weight", "insulin", "sugar", "glucose", "metabolic"],
        "ANDROGENIC": ["hair", "acne", "hirsutism", "skin", "jawline", "chin"],
        "PSYCHOLOGICAL": ["anxi", "mood", "stress", "depress", "irritab"],
    }
    identified = []
    for cluster, keywords in keyword_map.items():
        matches = [kw for kw in keywords if kw in text_lower]
        if matches:
            confidence = "high" if len(matches) >= 3 else "moderate" if len(matches) == 2 else "low"
            identified.append({
                "cluster_name": cluster,
                "identified_symptoms": matches,
                "reasoning": (
                    f"The narrative includes language related to {', '.join(matches)}, "
                    "which is commonly reported together in this cluster. Note: this "
                    "is pattern recognition, not diagnosis."
                ),
                "confidence": confidence,
            })

    return {
        "identified_clusters": identified,
        "unmatched_symptoms": [],
        "pattern_summary": (
            "[MOCK MODE — no API key set] The reported language may align with commonly "
            "co-occurring patterns. This is not a diagnosis. A healthcare professional "
            "must evaluate."
        ),
        "questions_for_doctor": [
            "What could be causing these symptoms?",
            "Would any tests help clarify what's going on?",
        ],
        "next_steps": (
            "Consider discussing these patterns with a healthcare provider who can "
            "perform proper diagnostic testing."
        ),
    }

def _get_client(api_key: str):
    import anthropic
    return anthropic.Anthropic(api_key=api_key)


def call_llm(narrative_text: str) -> dict:
    """
    Send a validated narrative to Claude and return the parsed JSON response.
    Retries a couple of times on failure. Falls back to mock mode if no API
    key is configured. Raises LLMError if the real call fails repeatedly.
    """
    api_key = _get_api_key()

    if not api_key:
        logger.warning("No API key configured — returning mock response.")
        return {
            "result": _mock_response(narrative_text),
            "mock": True,
        }

    system_prompt = build_system_prompt()
    last_error = None

    for attempt in range(1, MAX_RETRIES + 2):
        try:
            client = _get_client(api_key)
            response = client.messages.create(
                model=MODEL_NAME,
                max_tokens=MAX_TOKENS,
                system=system_prompt,
                messages=[{"role": "user", "content": narrative_text}],
            )

            raw_text = "".join(
                block.text for block in response.content if getattr(block, "type", None) == "text"
            ).strip()

            if raw_text.startswith("```"):
                raw_text = raw_text.strip("`")
                if raw_text.lower().startswith("json"):
                    raw_text = raw_text[4:].strip()

            parsed = json.loads(raw_text)
            _validate_schema(parsed)

            return {"result": parsed, "mock": False}

        except json.JSONDecodeError as exc:
            last_error = exc
            logger.warning("Claude returned non-JSON output on attempt %d: %s", attempt, exc)
        except Exception as exc:
            last_error = exc
            logger.warning("LLM call failed on attempt %d: %s", attempt, exc)

        if attempt <= MAX_RETRIES:
            time.sleep(0.5 * attempt)

    raise LLMError(f"LLM call failed after {MAX_RETRIES + 1} attempts: {last_error}")


def _validate_schema(parsed: dict) -> None:
    required_keys = {
        "identified_clusters", "unmatched_symptoms", "pattern_summary",
        "questions_for_doctor", "next_steps",
    }
    missing = required_keys - parsed.keys()
    if missing:
        raise LLMError(f"Claude's response is missing required keys: {missing}")

    for cluster in parsed["identified_clusters"]:
        if cluster.get("cluster_name") not in CLUSTER_NAMES:
            raise LLMError(f"Claude referenced an unknown cluster: {cluster.get('cluster_name')}")
        if cluster.get("confidence") not in {"low", "moderate", "high"}:
            raise LLMError(f"Claude used an invalid confidence value: {cluster.get('confidence')}")
