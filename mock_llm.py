"""Deterministic synthetic LLM tier for offline / no-key operation.

When ``NEBIUS_API_KEY`` is absent (or an offline/mock flag is set), the agent
should still run end-to-end for demos and CI instead of raising. This module
produces plausible, deterministic completions shaped like the real Nebius
responses (``{"content": ..., "role": "assistant", "tool_calls"?: [...]}``).

Stdlib-only — no ``openai`` / network. Nothing here is a real medical inference;
outputs are clearly labeled synthetic.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional


_DISCLAIMER = (
    "SYNTHETIC OUTPUT (offline mock tier — no live LLM). Not medical advice."
)


def _last_user_content(messages: List[Dict[str, Any]]) -> str:
    for msg in reversed(messages):
        if msg.get("role") == "user" and msg.get("content"):
            return str(msg["content"])
    return ""


def mock_chat(
    system_prompt: str,
    messages: List[Dict[str, Any]],
    tools: Optional[list] = None,
    tool_choice: Optional[str] = None,
    response_format: Optional[dict] = None,
) -> Dict[str, Any]:
    """Return a synthetic chat completion appropriate to the agent role.

    Role is inferred from the system prompt. When tools are offered and the
    prompt looks like the trial matcher, emits a synthetic tool call so the
    orchestrator's function-calling branch is exercised offline.
    """
    prompt = (system_prompt or "").lower()
    user = _last_user_content(messages)

    # Trial matcher: emit a tool call for search_clinical_trials.
    if tools and tool_choice == "auto" and "trial match" in prompt:
        # Derive a condition string from the user message heuristically.
        condition = "breast cancer"
        low = user.lower()
        if "prostate" in low:
            condition = "prostate cancer"
        elif "diagnosis:" in low:
            after = user.split("Diagnosis:", 1)[-1].split("\n", 1)[0].strip()
            condition = after or condition
        return {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "mock_call_1",
                    "type": "function",
                    "function": {
                        "name": "search_clinical_trials",
                        "arguments": json.dumps({"condition": condition}),
                    },
                }
            ],
        }

    # Orchestrator / synthesis: return a structured report skeleton. Checked
    # BEFORE the diagnostic branch because the orchestrator prompt also mentions
    # the diagnostic agent.
    if "orchestrator" in prompt or "synthesize" in user.lower():
        payload = {
            "patient_summary": "Synthetic summary generated offline.",
            "diagnosis_findings": "ER+/HER2- breast cancer (synthetic classification).",
            "matched_trials": [
                {
                    "nct_id": "NCT04200196",
                    "eligibility": "Likely eligible (synthetic assessment).",
                }
            ],
            "recommendations": "Discuss matched trials with the care team.",
            "disclaimers": _DISCLAIMER,
        }
        return {"role": "assistant", "content": json.dumps(payload)}

    # Diagnostic agent: return structured JSON classification.
    if "diagnostic" in prompt:
        payload = {
            "condition": "breast cancer",
            "subtype": "ER+/HER2- invasive ductal carcinoma",
            "confidence": 0.82,
            "key_findings": [
                "ER positive, HER2 negative",
                "Post-menopausal, ECOG 0",
            ],
            "_disclaimer": _DISCLAIMER,
        }
        return {"role": "assistant", "content": json.dumps(payload)}

    # Generic fallback.
    return {
        "role": "assistant",
        "content": json.dumps({"note": "synthetic response", "_disclaimer": _DISCLAIMER}),
    }


def mock_embed(texts: List[str], dim: int = 8) -> List[List[float]]:
    """Deterministic pseudo-embeddings (hash-based) for offline runs."""
    out = []
    for t in texts:
        h = abs(hash(t))
        vec = [((h >> (i * 4)) & 0xF) / 15.0 for i in range(dim)]
        out.append(vec)
    return out
