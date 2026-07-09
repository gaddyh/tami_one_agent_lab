from eval.metrics import keyword_hit


def test_keyword_hit_all_keywords():
    assert keyword_hit("Send a concise response", ["send", "response"])


def test_keyword_hit_missing_keyword():
    assert not keyword_hit("Send a concise response", ["deadline"])
