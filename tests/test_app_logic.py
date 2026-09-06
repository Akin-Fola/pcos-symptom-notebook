from app import build_annotated_html

def test_highlights_matching_symptom():
    text = "My period has been irregular for months."
    clusters = [
        {"cluster_name": "OVULATION", "identified_symptoms": ["period has been irregular"]},
    ]
    result = build_annotated_html(text, clusters)
    assert "background-color" in result
    assert "period has been irregular" in result


def test_no_match_returns_plain_text():
    text = "My period has been irregular for months."
    clusters = [
        {"cluster_name": "OVULATION", "identified_symptoms": ["something not in the text"]},
    ]
    result = build_annotated_html(text, clusters)
    assert "background-color" not in result
    assert "irregular" in result


def test_empty_clusters_returns_original_text():
    text = "Just some plain text here."
    result = build_annotated_html(text, [])
    assert "Just some plain text here." in result
