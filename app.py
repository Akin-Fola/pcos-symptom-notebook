import html
import json

import streamlit as st

from llm_client import LLMError, call_llm
from prompts import CLUSTER_LABELS
from validation import ValidationError, validate_narrative

CLUSTER_COLORS = {
    "OVULATION": "#2F5C4C",
    "METABOLIC": "#93611F",
    "ANDROGENIC": "#6B4066",
    "PSYCHOLOGICAL": "#3E5566",
}

def build_annotated_html(text: str, clusters: list) -> str:
    ranges = []
    for cluster in clusters:
        for symptom in cluster.get("identified_symptoms", []):
            idx = text.lower().find(str(symptom).lower())
            if idx != -1:
                ranges.append((idx, idx + len(symptom), cluster["cluster_name"]))

    ranges.sort(key=lambda r: r[0])
    non_overlapping = []
    last_end = -1
    for r in ranges:
        if r[0] >= last_end:
            non_overlapping.append(r)
            last_end = r[1]

    out = []
    cursor = 0
    for start, end, cluster_name in non_overlapping:
        out.append(html.escape(text[cursor:start]))
        color = CLUSTER_COLORS.get(cluster_name, "#333")
        segment = html.escape(text[start:end])
        out.append(f'<span style="background-color: {color}33; padding: 1px 2px; border-radius: 3px;">{segment}</span>')
        cursor = end
    out.append(html.escape(text[cursor:]))
    return "".join(out) or html.escape(text)

st.set_page_config(page_title="Symptom Pattern Notebook", page_icon="📝", layout="centered")

st.markdown(
    """
    <style>
    .stApp { background-color: #F5F4EF; }
    h1, h2, h3 { font-family: Georgia, serif; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Symptom Pattern Notebook")
st.write(
    "Write about your symptoms the way you'd describe them to a friend. This tool "
    "highlights phrases in your own words and shows, in plain language, how they "
    "relate to patterns sometimes discussed alongside PCOS — so you can bring a "
    "clearer picture to a healthcare professional, not a verdict."
)

st.warning(
    "**This is not a diagnosis.** Nothing here should be treated as medical advice. "
    "Only a healthcare professional can evaluate your symptoms properly."
)
if "result_data" not in st.session_state:
    st.session_state.result_data = None

narrative_input = st.text_area(
    "Describe what you've been noticing",
    height=180,
    max_chars=2000,
    placeholder="For example: My periods have been irregular for the past year, sometimes two months apart. I've also noticed...",
)

st.caption(f"{len(narrative_input)} / 1000 characters (recommended)")

submitted = st.button("Find patterns", type="primary")
if submitted:
    try:
        validated = validate_narrative(narrative_input)
    except ValidationError as exc:
        st.error(str(exc))
    else:
        with st.spinner("Reading your narrative and looking for patterns…"):
            try:
                llm_response = call_llm(validated["validated_text"])
            except LLMError:
                st.error("We couldn't process that narrative right now. Please try again shortly.")
            else:
                st.session_state.result_data = {
                    "narrative_text": validated["validated_text"],
                    "result": llm_response["result"],
                    "mock": llm_response.get("mock", False),
                }
if st.session_state.result_data:
    data = st.session_state.result_data
    result = data["result"]

    if data["mock"]:
        st.info("Demo mode: this result came from a simple keyword matcher, not Claude.")

    st.subheader("Your narrative")
    annotated = build_annotated_html(data["narrative_text"], result.get("identified_clusters", []))
    st.markdown(f'<div style="font-family: Georgia, serif; font-size: 18px; line-height: 1.8; background: #FBFAF6; border: 1px solid #DAD5C7; border-radius: 6px; padding: 20px;">{annotated}</div>', unsafe_allow_html=True)

    st.subheader("Patterns noted")
    clusters = result.get("identified_clusters", [])
    if not clusters:
        st.write("No clear patterns were identified from this narrative.")
    else:
        for cluster in clusters:
            label = CLUSTER_LABELS.get(cluster["cluster_name"], cluster["cluster_name"])
            with st.container(border=True):
                st.markdown(f"**{label}** — confidence: {cluster.get('confidence', '')}")
                st.write(cluster.get("reasoning", ""))

    st.subheader("Summary")
    st.write(result.get("pattern_summary", ""))

    questions = result.get("questions_for_doctor", [])
    if questions:
        st.subheader("Questions you could bring to your doctor")
        for question in questions:
            st.markdown(f"- {question}")

    st.subheader("Next steps")
    st.write(result.get("next_steps", ""))
