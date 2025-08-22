from dr_rd.retrieval.live_search import (
    OpenAIWebSearchClient,
    SerpAPIClient,
    get_live_client,
    Source,
)
from types import SimpleNamespace
from unittest.mock import patch


def test_openai_backend():
    fake_raw = SimpleNamespace(references=[{"title": "t", "url": "u"}])
    with patch("dr_rd.retrieval.live_search.call_openai") as mock:
        mock.return_value = {"text": "summary", "raw": fake_raw}
        client = OpenAIWebSearchClient()
        summary, sources = client.search_and_summarize("q", 5, 20)
        assert summary == "summary"
        assert sources[0].title == "t"


def test_serpapi_backend():
    with patch("dr_rd.retrieval.live_search.search_google") as sg, patch(
        "dr_rd.retrieval.live_search.summarize_search"
    ) as ss:
        sg.return_value = [{"snippet": "s", "title": "T", "link": "U"}]
        ss.return_value = "sum"
        client = SerpAPIClient()
        summary, sources = client.search_and_summarize("q", 5, 20)
        assert summary == "sum"
        assert sources[0].title == "T"


def test_get_live_client_fallback():
    client = get_live_client("unknown")
    assert isinstance(client, OpenAIWebSearchClient)
