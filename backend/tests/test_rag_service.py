from unittest.mock import MagicMock, patch

from app.services import rag_service


def _mock_embedding_response(vectors):
    response = MagicMock()
    response.data = [MagicMock(embedding=v) for v in vectors]
    return response


def test_embed_texts_empty_list_skips_api_call(app):
    with patch("app.services.rag_service.OpenAI") as mock_openai:
        result = rag_service.embed_texts([])

    assert result == []
    mock_openai.assert_not_called()


def test_embed_texts_returns_vectors_for_each_input(app):
    with patch("app.services.rag_service.OpenAI") as mock_openai:
        client = mock_openai.return_value
        client.embeddings.create.return_value = _mock_embedding_response(
            [[0.1, 0.2], [0.3, 0.4]]
        )

        result = rag_service.embed_texts(["a", "b"])

    assert result == [[0.1, 0.2], [0.3, 0.4]]
    client.embeddings.create.assert_called_once_with(
        model=rag_service.EMBEDDING_MODEL, input=["a", "b"]
    )


def test_embed_query_returns_single_vector(app):
    with patch("app.services.rag_service.OpenAI") as mock_openai:
        client = mock_openai.return_value
        client.embeddings.create.return_value = _mock_embedding_response([[1.0, 2.0]])

        result = rag_service.embed_query("hello")

    assert result == [1.0, 2.0]


def test_retrieve_returns_empty_for_unknown_exam(app, db):
    with patch("app.services.rag_service.embed_query") as mock_embed:
        result = rag_service.retrieve("anything", exam_code="ZZZ")

    assert result == []
    mock_embed.assert_not_called()
