from agent.tools import (
    generate_text,
    search_in_files,
    modify_data,
    save_output,
    get_storage_snapshot,
)


def test_generate_text_is_deterministic():
    payload = {"prompt": "Hello"}
    out1 = generate_text(payload)
    out2 = generate_text(payload)
    assert out1 == out2
    assert out1["text"].startswith("Generated: ")


def test_search_in_files_returns_mock_results():
    payload = {"query": "some interesting query"}
    out = search_in_files(payload)
    assert "results" in out
    assert len(out["results"]) >= 1


def test_search_in_files_empty_query_returns_no_results():
    out = search_in_files({"query": ""})
    assert out["results"] == []


def test_modify_data_echoes_and_summarises():
    payload = {"a": 1, "b": 2, "metadata": {"ignore": True}}
    out = modify_data(payload)
    assert "original" in out
    assert "summary" in out
    assert "metadata" not in out["original"]
    assert "Modified data with" in out["summary"]


def test_save_output_persists_data_with_incrementing_keys():
    payload = {"label": "test_item", "value": 42}
    result1 = save_output(payload)
    result2 = save_output(payload)

    assert result1["stored"] is True
    assert result2["stored"] is True
    assert result1["key"].startswith("test_item#")
    assert result2["key"].startswith("test_item#")
    assert result1["key"] != result2["key"]

    snapshot = get_storage_snapshot()
    assert result1["key"] in snapshot
    assert result2["key"] in snapshot



