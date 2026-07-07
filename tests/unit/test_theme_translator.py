from unittest.mock import MagicMock, patch

import pytest

from radar.agents.theme_translator import TranslationError, translate_theme_to_english


def _fake_client(output_text: str) -> MagicMock:
    client = MagicMock()
    response = MagicMock()
    response.output_text = output_text
    client.responses.create.return_value = response
    return client


@pytest.mark.asyncio
async def test_translates_portuguese_theme_to_english():
    with patch(
        "radar.agents.theme_translator.get_openai_client",
        return_value=_fake_client("AI-Assisted Industrial Maintenance"),
    ):
        result = await translate_theme_to_english("Manutenção Assistida por IA")
    assert result == "AI-Assisted Industrial Maintenance"


@pytest.mark.asyncio
async def test_theme_already_in_english_returned_unchanged():
    with patch(
        "radar.agents.theme_translator.get_openai_client",
        return_value=_fake_client("Edge AI"),
    ):
        result = await translate_theme_to_english("Edge AI")
    assert result == "Edge AI"


@pytest.mark.asyncio
async def test_result_is_stripped_of_surrounding_whitespace():
    with patch(
        "radar.agents.theme_translator.get_openai_client",
        return_value=_fake_client("  Digital Twins  "),
    ):
        result = await translate_theme_to_english("Gêmeos digitais")
    assert result == "Digital Twins"


@pytest.mark.asyncio
async def test_empty_translation_raises_translation_error():
    with patch(
        "radar.agents.theme_translator.get_openai_client",
        return_value=_fake_client(""),
    ):
        with pytest.raises(TranslationError):
            await translate_theme_to_english("Manutenção Assistida por IA")


@pytest.mark.asyncio
async def test_api_failure_raises_translation_error():
    client = MagicMock()
    client.responses.create.side_effect = RuntimeError("rate limited")
    with patch("radar.agents.theme_translator.get_openai_client", return_value=client):
        with pytest.raises(TranslationError):
            await translate_theme_to_english("Manutenção Assistida por IA")
