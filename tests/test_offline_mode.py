"""Offline / mock-tier tests for the MedPsy agent — run with ZERO credentials."""

import json

import pytest

import data_layer
from mock_llm import mock_chat, mock_embed
from nebius_client import NebiusAgent
from tools.trial_search import search_clinical_trials
from tools.ehr_lookup import ehr_lookup_patient


@pytest.fixture(autouse=True)
def _offline_env(monkeypatch):
    """Force full offline mode and a clean env for every test."""
    for var in ("NEBIUS_API_KEY", "MEDPSY_ALLOW_MOCK_TRIALS", "MEDPSY_MOCK"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("MEDPSY_OFFLINE", "1")


# ── mode detection ────────────────────────────────────────────────────────────
def test_offline_mode_detected():
    assert data_layer.offline_mode() is True
    assert data_layer.llm_available() is False


def test_llm_available_requires_key(monkeypatch):
    monkeypatch.delenv("MEDPSY_OFFLINE", raising=False)
    monkeypatch.delenv("NEBIUS_API_KEY", raising=False)
    assert data_layer.llm_available() is False
    monkeypatch.setenv("NEBIUS_API_KEY", "sk-test")
    assert data_layer.llm_available() is True


# ── synthetic trials fixture ──────────────────────────────────────────────────
def test_synthetic_trials_breast():
    trials = data_layer.synthetic_trials("ER+ HER2- breast cancer")
    assert len(trials) >= 1
    assert all(t["source"] == "synthetic" for t in trials)
    assert any("NCT" in t["nct_id"] for t in trials)


def test_synthetic_trials_default_fallback():
    trials = data_layer.synthetic_trials("some unlisted rare condition")
    assert len(trials) >= 1
    assert trials[0]["source"] == "synthetic"


# ── trial search tiers ────────────────────────────────────────────────────────
def test_trial_search_offline_returns_labeled_synthetic():
    # MEDPSY_OFFLINE=1 is an explicit opt-in to offline demo -> synthetic allowed,
    # but always clearly labeled as not-real.
    out = json.loads(search_clinical_trials("breast cancer"))
    assert out["count"] >= 1
    assert out["source"] == "synthetic"
    assert "SYNTHETIC" in out["note"]


def test_trial_search_online_failure_without_optin_is_safe_empty(monkeypatch, tmp_path):
    # Online (not offline) but network fails and no opt-in -> NO fabricated trials.
    monkeypatch.delenv("MEDPSY_OFFLINE", raising=False)
    monkeypatch.delenv("MEDPSY_MOCK", raising=False)
    monkeypatch.delenv("MEDPSY_ALLOW_MOCK_TRIALS", raising=False)
    monkeypatch.setenv("MEDPSY_CACHE_DIR", str(tmp_path / "cache_empty"))

    import tools.trial_search as ts

    def _boom(_url):
        raise RuntimeError("network down")

    monkeypatch.setattr(ts, "_fetch_trials", _boom)
    out = json.loads(ts.search_clinical_trials("breast cancer"))
    assert out["count"] == 0
    assert out["trials"] == []
    assert "note" in out


def test_trial_search_online_failure_with_optin_returns_synthetic(monkeypatch, tmp_path):
    monkeypatch.delenv("MEDPSY_OFFLINE", raising=False)
    monkeypatch.setenv("MEDPSY_ALLOW_MOCK_TRIALS", "1")
    monkeypatch.setenv("MEDPSY_CACHE_DIR", str(tmp_path / "cache_empty2"))

    import tools.trial_search as ts

    def _boom(_url):
        raise RuntimeError("down")

    monkeypatch.setattr(ts, "_fetch_trials", _boom)
    out = json.loads(ts.search_clinical_trials("prostate cancer"))
    assert out["count"] >= 1
    assert out["source"] == "synthetic"


# ── EHR lookup (already offline-safe demo data) ───────────────────────────────
def test_ehr_lookup_known_patient():
    out = json.loads(ehr_lookup_patient("P001"))
    assert out["patient"]["id"] == "P001"
    assert out["source"].startswith("EHR")


def test_ehr_lookup_unknown_patient():
    out = json.loads(ehr_lookup_patient("ZZZ"))
    assert "error" in out


# ── mock LLM tier ─────────────────────────────────────────────────────────────
def test_nebius_agent_offline_chat_returns_synthetic():
    agent = NebiusAgent(system_prompt="You are a clinical diagnostic AI agent.")
    assert agent.offline is True
    result = agent.chat(messages=[{"role": "user", "content": "Analyze patient"}])
    assert result["role"] == "assistant"
    payload = json.loads(result["content"])
    assert "subtype" in payload


def test_nebius_agent_offline_never_needs_key():
    # Construction must not raise despite no NEBIUS_API_KEY.
    agent = NebiusAgent(system_prompt="You are a clinical trial matching AI.")
    result = agent.chat(
        messages=[{"role": "user", "content": "Diagnosis: breast cancer"}],
        tools=[{"type": "function", "function": {"name": "search_clinical_trials"}}],
        tool_choice="auto",
    )
    assert "tool_calls" in result
    assert result["tool_calls"][0]["function"]["name"] == "search_clinical_trials"


def test_mock_embed_deterministic():
    a = mock_embed(["hello"])
    b = mock_embed(["hello"])
    assert a == b
    assert len(a[0]) == 8


def test_mock_chat_diagnostic_shape():
    r = mock_chat("You are a clinical diagnostic AI agent.", [{"role": "user", "content": "x"}])
    assert "content" in r
