"""
Clinical trial search tool for Nebius function calling.
Queries ClinicalTrials.gov API v2.
"""
import json
import os
import sys
import urllib.request
import urllib.parse
from typing import Optional

try:
    from cubiczan_resilience import resilient
except Exception:  # pragma: no cover - git dep may be absent offline/CI
    def resilient(*_args, **_kwargs):  # type: ignore
        def _decorator(fn):
            return fn

        if _args and callable(_args[0]) and not _kwargs:
            return _args[0]
        return _decorator

# Make the repo root importable so the shared data layer resolves whether this
# tool is imported as ``tools.trial_search`` or run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_layer import (  # noqa: E402
    mock_trials_allowed,
    offline_mode,
    read_cache,
    synthetic_trials,
    write_cache,
)


@resilient(timeout=20.0, max_attempts=3)
def _fetch_trials(url: str) -> dict:
    """Fetch and parse the ClinicalTrials.gov response (with retry/timeout)."""
    req = urllib.request.Request(url, headers={"User-Agent": "MedPsyAgent/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def search_clinical_trials(
    condition: str,
    age_range: Optional[str] = None,
    gender: Optional[str] = None,
    location: Optional[str] = None,
    ecog_status: Optional[str] = None,
    status: str = "RECRUITING",
    max_results: int = 5,
) -> str:
    """
    Search ClinicalTrials.gov for matching trials.

    Args:
        condition: Medical condition
        age_range: Patient age
        gender: Patient gender
        location: Geographic location
        ecog_status: ECOG performance status
        status: Trial recruitment status
        max_results: Maximum results to return

    Returns:
        JSON string of matching trials
    """
    # Use the v2 studies API
    base_url = "https://classic.clinicaltrials.gov/api/query/study_fields"
    query = f"AREA[Condition] {condition}"
    if location:
        query += f" AND AREA[LocationCity] {location}"

    params = {
        "expr": query,
        "fields": "NCTId,BriefTitle,Condition,OverallStatus,StartDate,PrimaryCompletionDate",
        "min_rnk": 1,
        "max_rnk": max_results,
        "fmt": "json",
    }

    cache_key = f"trials::{condition}::{location}::{max_results}"

    def _synthetic(reason: str) -> str:
        """Tier 3: opt-in, clearly-labeled synthetic trials from the fixture."""
        trials = synthetic_trials(condition, max_results)
        return json.dumps(
            {
                "trials": trials,
                "count": len(trials),
                "source": "synthetic",
                "note": (
                    "SYNTHETIC demo data — not a live ClinicalTrials.gov result. "
                    f"Reason: {reason}."
                ),
            },
            indent=2,
        )

    # ── Tier 0: fully offline — never touch the network. Synthetic is opt-in. ──
    if offline_mode():
        if mock_trials_allowed():
            return _synthetic("offline mode")
        return json.dumps(
            {
                "trials": [],
                "count": 0,
                "note": (
                    "Offline mode with synthetic trials disabled. Set "
                    "MEDPSY_MOCK=1 (or MEDPSY_ALLOW_MOCK_TRIALS=1) to enable "
                    "synthetic demo data."
                ),
            },
            indent=2,
        )

    # ── Tier 1: live ClinicalTrials.gov (retried + timeout-bounded). ──────────
    try:
        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        data = _fetch_trials(url)

        study_fields = data.get("StudyFieldsResponse", {}).get("StudyFieldsList", [])
        trials = []
        for study in study_fields:
            trials.append({
                "nct_id": (study.get("NCTId") or [""])[0],
                "title": (study.get("BriefTitle") or [""])[0],
                "status": (study.get("OverallStatus") or [""])[0],
                "condition": (study.get("Condition") or [""])[0],
            })

        result = json.dumps(
            {"trials": trials, "count": len(trials), "source": "live"}, indent=2
        )
        write_cache(cache_key, result)  # populate the cache tier on success
        return result

    except Exception as e:
        # ── Tier 2: local cache from a prior successful live query. ───────────
        cached = read_cache(cache_key)
        if cached is not None:
            return cached

        # ── Tier 3: synthetic — OPT-IN only. Fabricated trials are unsafe in a
        # clinical context (audit finding: "silent fallback to fabricated mock
        # data"), so default behaviour surfaces a structured error instead. ──
        if not mock_trials_allowed():
            return json.dumps(
                {
                    "trials": [],
                    "count": 0,
                    "error": str(e),
                    "note": (
                        "Live ClinicalTrials.gov lookup failed and no cache is "
                        "available. Set MEDPSY_ALLOW_MOCK_TRIALS=1 (or "
                        "MEDPSY_MOCK=1) to return synthetic demo data."
                    ),
                },
                indent=2,
            )
        return _synthetic(f"live lookup failed: {e}")


TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "search_clinical_trials",
        "description": "Search for clinical trials matching a patient's condition and demographics",
        "parameters": {
            "type": "object",
            "properties": {
                "condition": {"type": "string", "description": "The medical condition to search for"},
                "age_range": {"type": "string", "description": "Patient age"},
                "gender": {"type": "string", "enum": ["male", "female", "all"]},
                "location": {"type": "string", "description": "Geographic location"},
                "ecog_status": {"type": "string", "description": "ECOG performance status"},
                "status": {"type": "string", "enum": ["RECRUITING", "ACTIVE", "COMPLETED", "ALL"]},
            },
            "required": ["condition"],
        },
    },
}
