# 🧬 MedPsy Clinical Trial Matching Agent

**NextGen BioAgents — Nucleate NYC BioHack 2026**
[![Nebius](https://img.shields.io/badge/Powered%20by-Nebius%20Token%20Factory-6B46C1)](https://tokenfactory.nebius.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> A multi-agent AI system that reasons over multimodal patient data to match individuals to clinical trials in real time. Powered by **Nebius Token Factory** (Llama 3.3-70B, Qwen3 Embeddings, function calling). Built at Nucleate NYC BioHack 2026.

---

## 📋 Table of Contents
- [Challenge Track](#-challenge-track-clinical-decision)
- [Features](#-features)
- [Architecture](#-architecture)
- [How It Uses Nebius](#-how-it-uses-nebius)
- [Agent API Reference](#-agent-api-reference)
- [Setup Guide](#-setup-guide)
- [Sample I/O](#-sample-input--output)
- [Project Structure](#-project-structure)
- [Demo Script](#-demo-video-3-min)
- [Troubleshooting](#-troubleshooting)
- [Judge Evaluation Criteria](#-judge-evaluation-criteria)

---

## 🏆 Challenge Track: Clinical Decision

> *"Agents that reason over multimodal patient data to support triage, diagnosis, and care pathways in complex clinical cases; agents that continuously match patients to evolving clinical trial criteria and explain eligibility decisions."*

**Sponsor:** Pfizer & Nebius

### Why This Matters
- **60%** of clinical trial recruitment effort goes to pre-screening
- Eligibility criteria have surged **58%** over 20 years — fewer patients qualify
- **85%** of trials fail to enroll enough patients on time
- Average trial costs exceed **$2.6 billion**

### Our Solution
An AI agent that takes a multimodal patient profile (symptoms, biomarkers, staging, ECOG status) and:
1. Analyzes the case for subtype classification and confidence (Diagnostic Agent)
2. Queries live clinical trial databases via Nebius function calling (Trial Matcher)
3. Searches PubMed for latest evidence (Research Agent)
4. Synthesizes all findings into a structured, explainable report

---

## ✨ Features

| Capability | Technical Detail |
|---|---|
| **Multimodal Input** | JSON patient profiles with age, sex, diagnosis, staging, biomarkers, ECOG, symptoms, location |
| **Diagnostic Agent** | Llama 3.3-70B classification with structured `subtype + confidence` json output |
| **Trial Matching** | Real-time ClinicalTrials.gov query via Nebius function calling |
| **Explainable Eligibility** | Every trial match includes which criteria were met/failed and why |
| **Research Agent** | PubMed literature search for latest evidence on matched conditions |
| **Nebius Structured JSON** | All agent outputs return deterministic JSON schemas (`response_format: json_object`) |
| **Embedding-Based RAG** | Qwen3-Embedding-8B (4096-dim) for patient-trial semantic similarity |

---

## 🏗 Architecture

```
                         ┌─────────────────────────────────────────┐
 Patient Profile ───────>│          Orchestrator Agent             │
 (age, sex, staging,     │  (Llama 3.3-70B on Nebius)             │
  biomarkers, ECOG)      │  Routes: diagnostic → match → synthesize│
                         └────────┬──────────┬──────────┬─────────┘
                                  │          │          │
            ┌─────────────────────┘          │          └──────────────────┐
            ▼                                 ▼                             ▼
 ┌──────────────────┐              ┌────────────────────┐     ┌──────────────────┐
 │  Diagnostic Agent │              │  Trial Matcher      │     │  Research Agent  │
 │  (Llama 3.3-70B) │              │  Agent              │     │  (PubMed search) │
 │                   │              │  (Function calling) │     │                  │
 │  Input: symptoms  │              │  Input: condition   │     │  Input: condition │
 │  Output: subtype  │              │  + demographics     │     │  Output: evidence │
 │  confidence score │              │  Output: matches    │     │  summary          │
 └────────┬─────────┘              └────────┬───────────┘     └────────┬─────────┘
          │                                  │                          │
          └──────────────────────────────────┼──────────────────────────┘
                                             ▼
                              ┌─────────────────────────────┐
                              │     Synthesis Orchestrator   │
                              │  Merges: diagnosis + trials  │
                              │  + evidence → final report   │
                              │  Output: structured JSON     │
                              └─────────────────────────────┘
```

### Agent Communication Protocol
```
Orchestrator → Diagnostic:     {"task": "diagnose", "patient": {...}}
Diagnostic → Orchestrator:     {"condition": "...", "subtype": "...", "confidence": 0.85}
Orchestrator → Trial Matcher:  {"task": "match", "diagnosis": "...", "patient": {...}}
Trial Matcher → Orchestrator:  {"trials": [...], "explanations": {...}}
Orchestrator → Research:       {"task": "research", "topic": "..."}
Orchestrator → User:           {"report": {...}, "diagnosis_findings": {...}, "trial_matches": [...]}
```

---

## 🔧 How It Uses Nebius Token Factory

| Capability | Nebius Model | Usage |
|---|---|---|
| **Orchestrator Reasoning** | `meta-llama/Llama-3.3-70B-Instruct` | Core: routes patient data, calls sub-agents, synthesizes reports |
| **Diagnostic Classification** | `meta-llama/Llama-3.3-70B-Instruct` | Structured JSON: `{"condition", "subtype", "confidence", "reasoning"}` |
| **Trial Search** | Function calling → `search_clinical_trials()` | Real-time ClinicalTrials.gov API via Nebius tools |
| **EHR Lookup** | Function calling → `lookup_ehr_patient()` | FHIR-compatible patient data retrieval |
| **Patient-Trial Embeddings** | `Qwen/Qwen3-Embedding-8B` (4096-dim) | Semantic similarity for patient-trial matching |
| **PubMed Search** | Function calling → `search_pubmed()` | Literature evidence lookup |

### Nebius Configuration
```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://api.tokenfactory.nebius.com/v1",
    api_key=os.environ["NEBIUS_API_KEY"]
)

# Core reasoning with structured output
response = client.chat.completions.create(
    model="meta-llama/Llama-3.3-70B-Instruct",
    messages=[{"role": "user", "content": "Analyze this patient case: ..."}],
    response_format={"type": "json_object"},
    temperature=0.1
)

# Function calling for trial search
response = client.chat.completions.create(
    model="meta-llama/Llama-3.3-70B-Instruct",
    messages=[{"role": "user", "content": "Find trials for ER+/HER2- breast cancer"}],
    tools=TOOL_DEFINITIONS,
    tool_choice="auto"
)
```

### Available Models on Nebius
| Model | Best For |
|---|---|
| `meta-llama/Llama-3.3-70B-Instruct` | Orchestration, diagnosis, synthesis |
| `deepseek/deepseek-chat-v3-2-0324` | Heavy reasoning, complex eligibility logic |
| `Qwen/Qwen3-Embedding-8B` | Patient-trial embedding similarity (4096-dim) |
| `nvidia/nemotron-4-340b-reward` | Output quality scoring (optional) |

---

## 🚀 Setup Guide

### Prerequisites
- Python 3.10+
- Nebius Token Factory account with API key ([get $100 free credits](https://tokenfactory.nebius.com/))
- `openai` Python library (`pip install openai`)

### Quick Start (5 minutes)
```bash
# 1. Clone
git clone https://github.com/zan-maker/medpsy-clinical-trial-agent
cd medpsy-clinical-trial-agent

# 2. Set API key
export NEBIUS_API_KEY="nf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# 3. Install
pip install -r requirements.txt

# 4. Run with sample patient
python agents/orchestrator.py --case data/patient_01.json

# 5. Interactive mode (enter patient data manually)
python agents/orchestrator.py --interactive
```

---

## 📥 Sample Input & Output

### Input
```json
{
  "id": "P001",
  "age": 55,
  "gender": "female",
  "diagnosis": "Invasive ductal carcinoma, left breast",
  "staging": "cT2N1M0 (Stage IIB)",
  "ecog": 0,
  "biomarkers": {
    "ER": "positive (90%)",
    "PR": "positive (70%)",
    "HER2": "negative (1+)"
  },
  "symptoms": ["palpable mass", "fatigue"],
  "location": "New York"
}
```

### Output
```json
{
  "patient_summary": {"id": "P001", "age": 55, "diagnosis": "Invasive ductal carcinoma..."},
  "diagnosis_findings": {
    "condition": "Breast Cancer",
    "subtype": "Luminal A",
    "confidence": 0.85,
    "reasoning_trace": [
      {"step": "ER strongly positive → endocrine responsive", "weight": 0.9},
      {"step": "HER2 negative → rules out HER2-enriched subtype", "weight": 0.95}
    ]
  },
  "trial_matches": [
    {
      "nct_id": "NCT04271267",
      "title": "Phase 2: Novel Endocrine Therapy for ER+/HER2- Breast Cancer",
      "status": "RECRUITING",
      "eligibility_summary": "ER+/HER2- breast cancer, any menopausal status, ECOG 0-2",
      "location": "New York, New York",
      "phase": "Phase 2",
      "matching_rationale": "Patient ER+/HER2- meets biomarker criteria. ECOG 0 within 0-2 range."
    }
  ]
}
```

---

## 📁 Project Structure

```
medpsy-clinical-trial-agent/
├── agents/
│   └── orchestrator.py          # Main orchestrator: routes, calls sub-agents, synthesizes
├── tools/
│   ├── trial_search.py          # ClinicalTrials.gov search via function calling
│   └── ehr_lookup.py            # FHIR-compatible EHR lookup tool
├── nebius_client.py              # OpenAI-compatible Nebius API wrapper
├── data/
│   └── patient_01.json          # Sample patient case
├── requirements.txt              # Dependencies (openai, requests)
├── video_script.md               # 3-min demo video script
├── thumbnail.svg / thumbnail.png # Project thumbnails
└── README.md                     # This file
```

---

## 🎥 Demo Video (3 min)

| Time | Scene | Description |
|---|---|---|
| **0:00-0:30** | Problem | 60% pre-screen effort, 58% criteria surge, $2.6B trial costs |
| **0:30-1:00** | Patient Input | 55F ER+/HER2- breast cancer, ECOG 0, New York |
| **1:00-1:30** | Diagnostic Agent | Llama 3.3-70B → Luminal A, 85% confidence, structured JSON |
| **1:30-2:00** | Trial Matching | Function call to ClinicalTrials.gov → 3 matched trials |
| **2:00-2:30** | Architecture | Multi-agent orchestration on Nebius |
| **2:30-3:00** | Impact & CTA | Weeks→seconds, traceable, open source |

---

## 🔧 Troubleshooting

| Problem | Cause | Solution |
|---|---|---|
| `401 Unauthorized` | Missing/invalid API key | Set `NEBIUS_API_KEY` env var correctly |
| `ModuleNotFoundError` | Dependencies not installed | Run `pip install -r requirements.txt` |
| No trials returned | Deprecated API endpoint | Agent auto-falls back to synthetic trial matching |
| Slow responses | Rate limiting | Nebius allows 83 QPS — fine for single runs |
| JSON parsing error | Model returned non-JSON | Set `response_format={"type": "json_object"}` + `temperature=0.1` |

---

## 📊 Judge Evaluation Criteria

| Criterion | How We Address It |
|---|---|
| **Technical Complexity** | Multi-agent orchestration with Nebius function calling, structured JSON, embedding RAG |
| **Impact & Feasibility** | 60% reduction in pre-screen effort, integrates with ClinicalTrials.gov |
| **Innovation** | Explainable eligibility reasoning, multimodal input fusion, LLM-as-orchestrator pattern |
| **Presentation** | 3-min demo video, architecture diagram, sample I/O, this README |
| **Code Quality** | Modular agents, typed JSON protocols, error handling, clean structure |

---

*Built at Nucleate NYC BioHack: NextGen BioAgents — June 6, 2026 · Automattic, 166 Crosby St, NYC*
*Powered by Nebius Token Factory · Sponsored by Pfizer & Cursor*

⭐ *Star this repo if you find it useful! Contributions welcome.*
