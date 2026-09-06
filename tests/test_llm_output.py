import json

from llm_client import call_llm

SAMPLE_NARRATIVE = (
    "My periods have always been irregular, sometimes two or three months apart. "
    "I've also gained weight and have new facial hair along my jawline."
)


def test_response_is_json_serializable():
    response = call_llm(SAMPLE_NARRATIVE)
    json.dumps(response["result"])


def test_response_has_required_keys():
    result = call_llm(SAMPLE_NARRATIVE)["result"]
    for key in ("identified_clusters", "unmatched_symptoms", "pattern_summary", "questions_for_doctor", "next_steps"):
        assert key in result


def test_response_identifies_relevant_clusters():
    result = call_llm(SAMPLE_NARRATIVE)["result"]
    names = {c["cluster_name"] for c in result["identified_clusters"]}
    assert "OVULATION" in names
    assert "ANDROGENIC" in names


def test_mock_mode_is_free():
    response = call_llm(SAMPLE_NARRATIVE)
    assert response["mock"] is True
