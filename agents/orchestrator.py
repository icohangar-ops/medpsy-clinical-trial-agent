"""
MedPsy Clinical Trial Matching Agent — Main Orchestrator.

This agent runs the full pipeline:
1. Accept patient case (from EHR or manual input)
2. Diagnostic Agent analyzes symptoms/biomarkers
3. Trial Matcher queries ClinicalTrials.gov via function calling
4. Synthesize matched trials with eligibility rationale
5. Output structured JSON with traceable decisions

Powered by Nebius Token Factory.
"""

import os
import json
import sys

# Add the project root (parent of agents/) to path so nebius_client, tools/,
# and data_layer resolve whether run as a module or as a script.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nebius_client import NebiusAgent
from tools.trial_search import search_clinical_trials, TOOL_DEFINITION as TRIAL_TOOL
from tools.ehr_lookup import ehr_lookup_patient, TOOL_DEFINITION as EHR_TOOL

# Available tools for agents to call
AVAILABLE_TOOLS = {
    "search_clinical_trials": search_clinical_trials,
    "ehr_lookup_patient": ehr_lookup_patient,
}

TOOL_DEFINITIONS = [TRIAL_TOOL, EHR_TOOL]

# System prompts for each agent
ORCHESTRATOR_PROMPT = """You are a medical AI orchestrator. Your role:
1. Assess the patient case for clinical trial eligibility
2. Route to the diagnostic agent for subtype classification
3. Route to the trial matcher for querying ClinicalTrials.gov
4. Synthesize results into a clear, structured report

Always include medical disclaimers. Never provide treatment recommendations.
Output structured JSON with traceable reasoning."""

DIAGNOSTIC_PROMPT = """You are a clinical diagnostic AI agent. Analyze:
- Patient demographics (age, gender, ECOG)
- Biomarkers (ER/PR/HER2, genomic markers)
- Staging and progression
- Previous treatments

Classify the subtype, identify key biomarkers, and provide confidence scores.
Output structured JSON with condition, subtype, confidence, key_findings."""

TRIAL_MATCHER_PROMPT = """You are a clinical trial matching AI. Your role:
- Search ClinicalTrials.gov with the patient's specific condition and biomarkers
- Analyze eligibility criteria for each matched trial
- Determine if the patient qualifies (pass/fail each criterion)
- Return structured eligibility rationale

Use the search_clinical_trials function to query trials."""


def load_patient_case(filepath: str) -> dict:
    """Load a patient case from JSON file or create from manual input."""
    if os.path.exists(filepath):
        with open(filepath) as f:
            return json.load(f)
    # Default demo patient
    return {
        "id": "P001",
        "age": 55,
        "gender": "female",
        "diagnosis": "Invasive ductal carcinoma, left breast",
        "biomarkers": {
            "ER": "positive (90%)",
            "PR": "positive (70%)",
            "HER2": "negative (1+)",
        },
        "staging": "cT2N1M0 (Stage IIB)",
        "ecog": 0,
    }


def run_diagnostic_agent(patient: dict) -> dict:
    """Run the diagnostic agent to classify the cancer subtype."""
    agent = NebiusAgent(
        model="meta-llama/Llama-3.3-70B-Instruct",
        system_prompt=DIAGNOSTIC_PROMPT,
    )

    patient_str = json.dumps(patient, indent=2)
    result = agent.chat(
        messages=[
            {
                "role": "user",
                "content": f"Analyze this patient case and classify the cancer subtype:\n\n{patient_str}",
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
    )

    content = result.get("content", "{}")
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {"subtype": "unknown", "confidence": 0, "raw": content}


def run_trial_matcher(patient: dict, diagnosis: dict) -> dict:
    """Run the trial matcher to find matching clinical trials."""
    agent = NebiusAgent(
        model="meta-llama/Llama-3.3-70B-Instruct",
        system_prompt=TRIAL_MATCHER_PROMPT,
    )

    # Build a search query from patient + diagnosis
    condition = patient.get("diagnosis", "")
    biomarkers = patient.get("biomarkers", {})
    biomarker_str = "; ".join(f"{k}: {v}" for k, v in biomarkers.items())

    messages = [
        {
            "role": "user",
            "content": (
                f"Patient: {patient.get('age')}-year-old {patient.get('gender')}, "
                f"ECOG {patient.get('ecog')}\n"
                f"Diagnosis: {condition}\n"
                f"Biomarkers: {biomarker_str}\n"
                f"Location: New York\n\n"
                f"Search for matching clinical trials and determine eligibility."
                f"Use the search_clinical_trials function with the patient's condition."
            ),
        }
    ]

    # Run with function calling capability
    result = agent.chat(
        messages=messages,
        tools=TOOL_DEFINITIONS,
        tool_choice="auto",
        max_tokens=2000,
    )

    # Handle tool calls
    tool_results = []
    if result.get("tool_calls"):
        for tc in result["tool_calls"]:
            fn_name = tc["function"]["name"]
            fn_args = json.loads(tc["function"]["arguments"])
            if fn_name in AVAILABLE_TOOLS:
                tool_result = AVAILABLE_TOOLS[fn_name](**fn_args)
                tool_results.append(
                    {"function": fn_name, "args": fn_args, "result": tool_result}
                )

        # Feed tool results back for synthesis
        messages.append(
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": tc["id"],
                        "type": tc["type"],
                        "function": tc["function"],
                    }
                    for tc in result["tool_calls"]
                ],
            }
        )
        for tr in tool_results:
            messages.append(
                {
                    "role": "tool",
                    "content": tr["result"],
                    "tool_call_id": tr["function"],
                }
            )

        final_result = agent.chat(
            messages=messages,
            temperature=0.1,
            max_tokens=2000,
        )
        content = final_result.get("content", "{}")
    else:
        content = result.get("content", "{}")

    return {
        "diagnosis": diagnosis,
        "tool_calls": tool_results,
        "final_matches": content,
    }


def synthesize_report(patient: dict, trial_results: dict) -> str:
    """Synthesize everything into a final matching report."""
    agent = NebiusAgent(
        model="meta-llama/Llama-3.3-70B-Instruct",
        system_prompt=ORCHESTRATOR_PROMPT,
    )

    result = agent.chat(
        messages=[
            {
                "role": "user",
                "content": (
                    f"Synthesize this clinical trial matching into a final report.\n\n"
                    f"Patient: {json.dumps(patient, indent=2)}\n\n"
                    f"Matching Results: {json.dumps(trial_results, indent=2)}\n\n"
                    f"Produce a JSON report with: patient_summary, diagnosis_findings, "
                    f"matched_trials (with eligibility details for each), "
                    f"recommendations, and disclaimers."
                ),
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=2000,
    )

    return result.get("content", "{}")


def main():
    """Run the full MedPsy Clinical Trial Matching pipeline."""
    import argparse

    parser = argparse.ArgumentParser(
        description="MedPsy Clinical Trial Matching Agent"
    )
    parser.add_argument(
        "--case", "-c",
        default=None,
        help="Path to patient case JSON file. Uses demo patient if omitted.",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output file for the matching report (JSON)",
    )
    args = parser.parse_args()

    try:
        # Load patient case
        patient = load_patient_case(args.case) if args.case else load_patient_case("nonexistent")
        print(f"🧬 MedPsy Clinical Trial Matching Agent")
        print("=" * 50)
        print(f"Patient: {patient.get('age')}yo {patient.get('gender')} — {patient.get('diagnosis')}")
        print()

        # Step 1: Diagnostic analysis
        print("🔬 Step 1: Diagnostic Analysis...")
        diagnosis = run_diagnostic_agent(patient)
        print(f"  Subtype: {diagnosis.get('subtype', 'N/A')}")
        print(f"  Confidence: {diagnosis.get('confidence', 'N/A')}")
        print()

        # Step 2: Trial matching
        print("🔎 Step 2: Trial Matching...")
        trial_results = run_trial_matcher(patient, diagnosis)
        print(f"  Tool calls: {len(trial_results.get('tool_calls', []))}")
        print()

        # Step 3: Synthesize report
        print("📋 Step 3: Synthesizing Report...")
        report = synthesize_report(patient, trial_results)
        print()

        # Output
        try:
            report_json = json.loads(report)
            print("✅ Report Generated:")
            print(json.dumps(report_json, indent=2)[:2000])
        except json.JSONDecodeError:
            print("⚠️ Raw Report:")
            print(report[:2000])

        if args.output:
            with open(args.output, "w") as f:
                f.write(report)
            print(f"\n📁 Report saved to: {args.output}")

        return report

    except Exception as exc:
        # Emit a structured error JSON instead of a raw traceback so callers /
        # downstream tooling can parse the failure deterministically.
        error_payload = {
            "status": "error",
            "error_type": type(exc).__name__,
            "message": str(exc),
        }
        print(json.dumps(error_payload, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
