from unittest.mock import MagicMock, patch

import pytest

from radar.agents.scope_guard import ScopeCheckError, is_in_scope


def _fake_client(output_text: str) -> MagicMock:
    client = MagicMock()
    response = MagicMock()
    response.output_text = output_text
    client.responses.create.return_value = response
    return client


@pytest.mark.asyncio
async def test_in_scope_theme_returns_true():
    with patch("radar.agents.scope_guard.get_openai_client", return_value=_fake_client("SIM")):
        result = await is_in_scope("Edge AI")
    assert result is True


@pytest.mark.asyncio
async def test_out_of_scope_theme_returns_false():
    with patch("radar.agents.scope_guard.get_openai_client", return_value=_fake_client("NAO")):
        result = await is_in_scope("qual a capital da frança?")
    assert result is False


@pytest.mark.asyncio
async def test_answer_is_case_insensitive_and_trims_whitespace():
    with patch("radar.agents.scope_guard.get_openai_client", return_value=_fake_client("  sim  ")):
        result = await is_in_scope("Digital twins")
    assert result is True


@pytest.mark.asyncio
async def test_unexpected_answer_treated_as_out_of_scope():
    with patch("radar.agents.scope_guard.get_openai_client", return_value=_fake_client("talvez")):
        result = await is_in_scope("algo ambíguo")
    assert result is False


@pytest.mark.asyncio
async def test_api_failure_raises_scope_check_error():
    client = MagicMock()
    client.responses.create.side_effect = RuntimeError("rate limited")
    with patch("radar.agents.scope_guard.get_openai_client", return_value=client):
        with pytest.raises(ScopeCheckError):
            await is_in_scope("Edge AI")
