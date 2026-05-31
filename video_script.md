# 🎬 Demo Video Script — MedPsy Clinical Trial Matching Agent (3 min)

## [0:00 - 0:15] Hook
> Visual: Patient chart on screen. Clock ticking. Text: "60% of recruitment effort = pre-screening"
Narrator: "Clinical trial recruitment is broken. Pre-screening consumes 60% of effort. Eligibility criteria have surged 58% in 20 years. Most trials fail because they can't find the right patients fast enough."

## [0:15 - 0:30] Problem Framing
> Visual: Split screen — manual process (cluttered desk, papers) vs. automated
Narrator: "We built the MedPsy Clinical Trial Matching Agent — multi-agent AI on Nebius Token Factory that matches patients to trials in real-time."

## [0:30 - 1:00] Patient Input
> Visual: UI — input panel with age/sex/diagnosis/demo fields
Narrator: "Let's input a patient: 55-year-old female, ER+/HER2- breast cancer, ECOG 0, based in New York."
> Clicks submit. Agents activate — animation shows routing

## [1:00 - 1:30] Diagnostic Agent
> Visual: Nebius function calling in action — structured JSON on screen
Narrator: "The Diagnostic Agent analyzes the case via Llama 3.3-70B on Nebius. It classifies the breast cancer subtype, then calls ClinicalTrials.gov through Nebius function calling."

## [1:30 - 2:00] Trial Matcher
> Visual: Results appear — 3 matched trials with eligibility checklists
Narrator: "The Trial Matching Agent returns 3 trials with full eligibility rationale — which criteria passed, which failed, and why. Each decision is traceable."

## [2:00 - 2:30] Technical Deep Dive
> Visual: Architecture diagram — Orchestrator → Agents → Nebius API
Narrator: "Architecture: Multi-agent system on Nebius Token Factory. Llama 3.3-70B for reasoning. Qwen3 for embeddings. Function calling for external APIs. Structured JSON outputs for deterministic pipelines. Everything runs on Nebius with $100 in credits."

## [2:30 - 3:00] Impact & Close
> Visual: Call to action — "Built at Nucleate NYC BioHack 2026"
Narrator: "Impact: From weeks of manual matching to seconds. From opaque decisions to fully traceable rationale. From missed opportunities to every eligible patient found. Built with Nebius Token Factory — check our repo for the full architecture."
