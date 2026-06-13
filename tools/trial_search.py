"""
Clinical trial search tool for Nebius function calling.
Queries ClinicalTrials.gov API v2.
"""
import json
import os
import urllib.request
import urllib.parse
from typing import Optional

from cubiczan_resilience import resilient


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

    try:
        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        # Retried + timeout-bounded fetch (cubiczan_resilience). After max_attempts
        # the underlying exception propagates to the handler below.
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

        return json.dumps({"trials": trials, "count": len(trials)}, indent=2)

    except Exception as e:
        # The live ClinicalTrials.gov query failed after retries. Returning
        # fabricated trials as if they were real is unsafe in a clinical
        # context (audit finding: "silent fallback to fabricated mock data"),
        # so the synthetic demo dataset is now OPT-IN and explicitly labeled.
        # Default behaviour surfaces a structured error so callers do not
        # mistake invented trials for genuine matches.
        if os.environ.get("MEDPSY_ALLOW_MOCK_TRIALS") != "1":
            return json.dumps(
                {
                    "trials": [],
                    "count": 0,
                    "error": str(e),
                    "note": (
                        "Live ClinicalTrials.gov lookup failed. Set "
                        "MEDPSY_ALLOW_MOCK_TRIALS=1 to return synthetic demo data."
                    ),
                },
                indent=2,
            )

        # Explicitly opted-in synthetic demo data (clearly flagged as not real).
        mock_trials = [
            {
                "nct_id": "NCT04200196",
                "title": "A Study of Ibrance (Palbociclib) Plus Letrozole in Chinese Participants With ER+/HER2- Advanced Breast Cancer",
                "status": "RECRUITING",
                "condition": "ER+ HER2- Breast Cancer",
                "phase": "Phase 3",
                "eligibility_summary": "ER+/HER2- breast cancer, post-menopausal, ECOG 0-1",
                "location": "Multiple sites including New York",
            },
            {
                "nct_id": "NCT04949256",
                "title": "Ribociclib and Letrozole in Advanced ER+/HER2- Breast Cancer",
                "status": "RECRUITING",
                "condition": "ER+ HER2- Breast Cancer",
                "phase": "Phase 2",
                "eligibility_summary": "ER+/HER2- breast cancer, any menopausal status, ECOG 0-2",
                "location": "New York, NY",
            },
            {
                "nct_id": "NCT05563376",
                "title": "Abemaciclib in High-Risk Early Breast Cancer (monarchE)",
                "status": "ACTIVE",
                "condition": "ER+ HER2- High-Risk Early Breast Cancer",
                "phase": "Phase 3",
                "eligibility_summary": "ER+/HER2- breast cancer, 4+ positive nodes, ECOG 0-1",
                "location": "Multiple US sites",
            },
        ]
        return json.dumps({"trials": mock_trials, "count": len(mock_trials), "source": "mock", "error": str(e)}, indent=2)


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
