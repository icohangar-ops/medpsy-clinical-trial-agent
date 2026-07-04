"""Three-tier data + offline-mode support for the MedPsy agent.

Mirrors the Cubiczan donor pattern (finance-cockpit / market-radar): every data
fetch resolves through **live -> local cache -> embedded synthetic mock**, so the
agent boots, demos, and passes tests with **zero credentials**.

This module is intentionally dependency-free (stdlib only) so it imports cleanly
in CI and tests without ``openai``, ``nebius-client``, or the
``cubiczan-resilience`` git package installed.

Offline/mock mode is triggered by ANY of:
    * ``MEDPSY_OFFLINE=1``                              (explicit, everything mock)
    * ``MEDPSY_MOCK=1`` / ``MEDPSY_ALLOW_MOCK_TRIALS=1`` (allow synthetic trials)
    * missing ``NEBIUS_API_KEY``                        (auto-detect for the LLM)
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional

_FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
_TRIALS_FIXTURE = os.path.join(_FIXTURES_DIR, "synthetic_trials.json")
_CACHE_TTL_SECONDS = 6 * 60 * 60  # 6h


# ── mode detection ────────────────────────────────────────────────────────────
def offline_mode() -> bool:
    """True when the agent should run fully offline (no live API calls)."""
    return os.environ.get("MEDPSY_OFFLINE") == "1"


def llm_available() -> bool:
    """True when a live LLM (Nebius) can be called."""
    if offline_mode() or os.environ.get("MEDPSY_MOCK") == "1":
        return False
    return bool(os.environ.get("NEBIUS_API_KEY"))


def mock_trials_allowed() -> bool:
    """True when returning SYNTHETIC trial data is permitted.

    Fabricated trials are unsafe in a clinical context, so synthetic trial data
    stays opt-in (audit finding). Offline/mock flags opt in explicitly.
    """
    return (
        offline_mode()
        or os.environ.get("MEDPSY_MOCK") == "1"
        or os.environ.get("MEDPSY_ALLOW_MOCK_TRIALS") == "1"
    )


# ── synthetic trials (MOCK tier) ──────────────────────────────────────────────
def load_trial_fixture() -> Dict[str, Any]:
    with open(_TRIALS_FIXTURE, "r", encoding="utf-8") as fh:
        return json.load(fh)


def synthetic_trials(condition: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Return SYNTHETIC trials for a condition from the embedded fixture.

    Matches on any keyword overlap with the fixture's condition keys; falls back
    to the fixture's ``default`` list. Every returned trial is tagged
    ``source="synthetic"`` so callers can never mistake it for a live result.
    """
    fixture = load_trial_fixture()
    conditions = fixture.get("conditions", {})
    cond_lower = (condition or "").lower()

    chosen: Optional[List[Dict[str, Any]]] = None
    for key, trials in conditions.items():
        if key in cond_lower or any(tok in cond_lower for tok in key.split()):
            chosen = trials
            break
    if chosen is None:
        chosen = fixture.get("default", [])

    out = []
    for t in chosen[:max_results]:
        item = dict(t)
        item["source"] = "synthetic"
        out.append(item)
    return out


# ── local cache (CACHE tier) ──────────────────────────────────────────────────
def _cache_path(key: str) -> str:
    safe = "".join(c if c.isalnum() else "_" for c in key)[:80]
    base = os.environ.get("MEDPSY_CACHE_DIR", os.path.join(_FIXTURES_DIR, ".cache"))
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, f"{safe}.json")


def read_cache(key: str) -> Optional[Any]:
    path = _cache_path(key)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            wrapped = json.load(fh)
        if time.time() - wrapped.get("timestamp", 0) > _CACHE_TTL_SECONDS:
            return None
        return wrapped["data"]
    except Exception:
        return None


def write_cache(key: str, data: Any) -> None:
    try:
        with open(_cache_path(key), "w", encoding="utf-8") as fh:
            json.dump({"timestamp": time.time(), "data": data}, fh)
    except Exception:
        pass  # non-fatal
