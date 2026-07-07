import pytest

from radar.collectors.industrial_scope import needs_industrial_scoping


@pytest.mark.parametrize(
    "theme",
    [
        "IoT",
        "Edge AI",
        "Manutenção assistida por IA Generativa e Multiagentes de IA",
        "gêmeos digitais",
    ],
)
def test_needs_industrial_scoping_true_for_unqualified_theme(theme):
    assert needs_industrial_scoping(theme) is True


@pytest.mark.parametrize(
    "theme",
    [
        "IoT industrial",
        "IoT Industrial",
        "Robôs Humanoides para Indústria",
        "Manutenção preditiva na manufatura",
        "Digital twins in Industry 4.0",
        "Sensores no chão de fábrica",
    ],
)
def test_needs_industrial_scoping_false_when_already_qualified(theme):
    assert needs_industrial_scoping(theme) is False
