"""End-to-end offline smoke test: the full orchestrator pipeline with no keys."""

import json

import pytest


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    monkeypatch.delenv("NEBIUS_API_KEY", raising=False)
    monkeypatch.setenv("MEDPSY_OFFLINE", "1")
    monkeypatch.setenv("MEDPSY_MOCK", "1")


def test_full_pipeline_runs_offline():
    from agents import orchestrator as orch

    patient = orch.load_patient_case("nonexistent")  # -> demo patient
    diagnosis = orch.run_diagnostic_agent(patient)
    assert isinstance(diagnosis, dict)

    trial_results = orch.run_trial_matcher(patient, diagnosis)
    # Offline trial matcher emits a synthetic tool call that hits the fixture.
    assert "tool_calls" in trial_results
    assert len(trial_results["tool_calls"]) >= 1

    report = orch.synthesize_report(patient, trial_results)
    parsed = json.loads(report)
    assert "matched_trials" in parsed
    assert "disclaimers" in parsed
