# 🧬 MedPsy Clinical Trial Matching Agent

**NextGen BioAgents — Nucleate NYC BioHack 2026**
[![Nebius](https://img.shields.io/badge/Powered%20by-Nebius%20Token%20Factory-6B46C1)](https://tokenfactory.nebius.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> An AI agent that reasons over multimodal patient data to match individuals to clinical trials in real-time — powered by Nebius Token Factory inference.

---

## 🏆 Challenge Track: Clinical Decision

> *"Agents that reason over multimodal patient data to support triage, diagnosis, and care pathways in complex clinical cases; agents that continuously match patients to evolving clinical trial criteria and explain eligibility decisions."*

## 🚀 Built With

| Component | Technology |
|-----------|-----------|
| **LLM Inference** | [Nebius Token Factory](https://tokenfactory.nebius.com/) — Llama 3.3-70B-Instruct |
| **Embeddings / RAG** | Nebius Qwen3-Embedding-8B + PGVector |
| **Agent Framework** | Multi-agent orchestration (Orchestrator → Diagnostic / Trial Match / Research) |
| **Function Calling** | Nebius native function calling for EHR lookup, trial database query |
| **Frontend** | Electron + React 18 + TypeScript (forked from MedPsy Edge Agent) |
| **EHR Interop** | FHIR R4 API via function tools |

## ✨ Key Features

| Capability | Details |
|---|---|
| **Multimodal Input** | Accepts symptoms, lab values, imaging reports, and free-text clinical notes |
| **Real-Time Trial Matching** | Queries ClinicalTrials.gov + Pfizer trial database for active enrollments |
| **Explainable Eligibility** | Every match includes a traceable eligibility rationale — which criteria met, which failed, why |
| **Care Gap Detection** | Surfaces patients who qualify for trials but haven't been identified |
| **Privacy-First** | Nebius inference with no patient data persisted — all processing is ephemeral |

## 🏗 Architecture

```
                                          ┌─────────────────┐
  Patient Data ──────────────────────────>│   Orchestrator   │
  (EHR, labs, notes, imaging)             │  (Llama 3.3-70B) │
                                          └───┬───┬───┬─────┘
                                              │   │   │
                    ┌─────────────────────────┘   │   └──────────────────┐
                    ▼                             ▼                      ▼
          ┌─────────────────┐          ┌──────────────────┐    ┌──────────────────┐
          │   Diagnostic    │          │  Trial Matching  │    │   Research       │
          │     Agent       │          │     Agent        │    │    Agent         │
          │ (Symptom→Dx     │          │ (Criteria→Trials)│    │ (Literature→     │
          │  reasoning)     │          │                  │    │  Evidence)       │
          └────────┬────────┘          └────────┬─────────┘    └────────┬─────────┘
                   │                          │                        │
                   ▼                          ▼                        ▼
           ┌──────────────┐         ┌──────────────────┐      ┌──────────────┐
           │Diagnosis     │         │ Matched Trials   │      │ Evidence     │
           │ + Confidence │         │ + Eligibility    │      │ Summary      │
           └──────────────┘         │ Rationale        │      └──────────────┘
                                    └──────────────────┘
```

## 🔧 How It Uses Nebius Token Factory

1. **Llama 3.3-70B-Instruct** — Core reasoning engine for the orchestrator and all specialist agents
2. **Function Calling** — Agents call EHR lookup tools, clinical trial database queries, and PubMed search via Nebius's OpenAI-compatible API
3. **Qwen3-Embedding-8B** — Patient notes and trial criteria embedded for semantic similarity matching
4. **Structured JSON Outputs** — All agent responses return structured JSON for deterministic downstream processing

## 🎥 Demo Video (3 min)

[Watch the demo →](https://youtube.com/...) (placeholder - 3-min walkthrough)

### Script Outline:
1. **0:00-0:30** — Problem: 60% of clinical trial recruitment effort is pre-screening. 58% surge in eligibility criteria over 20 years.
2. **0:30-1:15** — Input a sample patient case (multimodal: symptoms + lab values + notes)
3. **1:15-2:00** — Agent runs diagnosis + real-time clinical trial query via Nebius function calling
4. **2:00-2:30** — Results: matched trials with eligibility rationale, care gaps detected
5. **2:30-3:00** — Architecture deep-dive: multi-agent on Nebius, privacy, extensibility

## 📁 Repo Structure

```
medpsy-clinical-trial-agent/
├── agents/
│   ├── orchestrator.py        # Llama 3.3-70B orchestration agent
│   ├── diagnostic.py          # Symptom → diagnosis reasoning
│   ├── trial_matcher.py       # Clinical trial eligibility engine
│   └── research.py            # Literature evidence agent
├── tools/
│   ├── ehr_lookup.py          # FHIR-compatible EHR tool
│   ├── trial_query.py         # ClinicalTrials.gov + Pfizer DB tool
│   └── pubmed_search.py       # PubMed literature search
├── frontend/                  # Electron + React UI (forked)
├── nebius/
│   └── client.py              # Nebius API client wrapper
├── data/
│   └── sample_cases/          # Demo patient cases
└── README.md
```

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/cubiczan/medpsy-clinical-trial-agent
cd medpsy-clinical-trial-agent

# Set up Nebius
export NEBIUS_API_KEY="your-key-here"

# Install dependencies
pip install -r requirements.txt

# Run the agent
python agents/orchestrator.py --case data/sample_cases/patient_01.json
```

## 📊 Awards & Recognition

**BioHack Track:** Clinical Decision
**Sponsor:** Pfizer (proposed challenge tracks), Nebius (solutions sponsor)
**Prizes:** Cash + Nebius cloud credits + Cursor credits

---

*Built at Nucleate NYC BioHack: NextGen BioAgents — June 6, 2026*
