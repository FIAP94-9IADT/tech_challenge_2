"""
Testes para o módulo LLM.
Usa mocks para não depender de chave de API nos testes automatizados.
"""
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.llm.prompts import build_diagnosis_prompt, SYSTEM_PROMPT


def test_system_prompt_not_empty():
    assert len(SYSTEM_PROMPT) > 100


def test_build_diagnosis_prompt_contains_key_info():
    prompt = build_diagnosis_prompt(
        age_group="meia_idade",
        diagnosis_label="MALIGNO",
        prob_malignant=0.87,
        top_features=[("mean radius", 2.5), ("mean texture", 1.8), ("mean area", 3.1),
                      ("mean perimeter", 2.0), ("mean concavity", 1.5)],
        metrics={"sensibilidade": 0.95, "especificidade": 0.88, "f1_score": 0.91},
    )
    assert "meia_idade" in prompt
    assert "MALIGNO" in prompt
    assert "87.0%" in prompt
    assert "mean radius" in prompt


def test_build_diagnosis_prompt_includes_metrics():
    prompt = build_diagnosis_prompt(
        age_group="senior",
        diagnosis_label="BENIGNO",
        prob_malignant=0.12,
        top_features=[("mean radius", 1.0)],
        metrics={"sensibilidade": 0.90, "especificidade": 0.85, "f1_score": 0.87},
    )
    assert "90.0%" in prompt or "0.9" in prompt


@patch("src.llm.interpreter._get_client", return_value=None)
def test_generate_diagnosis_uses_mock_when_no_api_key(mock_client, tmp_path, monkeypatch):
    """Sem OPENAI_API_KEY, deve retornar resposta mock sem lançar exceção."""
    import src.llm.interpreter as interp

    monkeypatch.setattr(interp, "RESULTS_DIR", tmp_path)

    result = interp.generate_diagnosis_interpretation(
        age_group="jovem",
        diagnosis_label="BENIGNO",
        prob_malignant=0.05,
        top_features=[("mean radius", 1.2)],
        metrics={"sensibilidade": 0.9, "especificidade": 0.85, "f1_score": 0.87},
        save_response=True,
    )

    assert isinstance(result, str)
    assert len(result) > 50
    saved_files = list(tmp_path.glob("*.json"))
    assert len(saved_files) == 1


@patch("src.llm.interpreter._get_client", return_value=None)
def test_save_response_creates_json(mock_client, tmp_path, monkeypatch):
    import src.llm.interpreter as interp

    monkeypatch.setattr(interp, "RESULTS_DIR", tmp_path)
    interp._save_response(
        prompt_type="test",
        prompt="test prompt",
        response="test response",
        metadata={"key": "value"},
    )
    files = list(tmp_path.glob("test_*.json"))
    assert len(files) == 1
    with open(files[0]) as f:
        data = json.load(f)
    assert data["type"] == "test"
    assert data["prompt"] == "test prompt"
    assert data["response"] == "test response"
    assert data["metadata"]["key"] == "value"
