# CIRO (Crisis Intelligence & Response Orchestrator)
## Implementation & Technical Documentation

This document serves as the central record for the architecture, steps, and implementations executed during the hackathon. 

---

## 1. System Architecture Overview

CIRO is designed as a multi-agent orchestration system. Instead of relying on a single large LLM prompt to solve everything, CIRO breaks down the crisis management process into discrete, specialized agents using a pipeline approach.

### Core Pipeline Flow:
1. **Ingestion**: Raw signals (social, weather, sensors) hit the `/signals/ingest` endpoint.
2. **Normalization**: The signal is converted into a standard `NormalizedSignal`.
3. **Orchestration**: The `Orchestrator` is triggered via a background task. It passes the signal sequentially through the Antigravity agents.
4. **Agent Sequence**:
   - `SignalFusionAgent`: Geospatial clustering.
   - `CredibilityAgent`: Contradiction and source weighting.
   - `ClassificationAgent`: LLM-driven categorization and severity scoring.
   - `ResourceAllocationAgent`, `SimulationAgent`, `StakeholderMessagingAgent`, `RecoveryAgent`.
5. **Persistence & Broadcast**: The resulting `Incident` and all `AgentTrace` logs are saved to Firestore, and live updates are pushed to connected clients (e.g., Flutter app) via WebSockets.

---

## 2. Implemented Components (Day 1 & Day 2: Core Intelligence)

### A. Inter-Agent Data Models (`backend/models/agent_io.py`)
To ensure reliable communication between agents without hallucinatory errors, we implemented strict Pydantic schemas:
- **`IncidentContext`**: Groups multiple `NormalizedSignals` together. It acts as the "working memory" before an official `Incident` is committed.
- **`CredibilityReport`**: Stores the credibility scores of individual signals and flags if multiple signals contradict each other.

### B. Base Agent Framework (`backend/agents/base.py`)
We created a `BaseAgent` abstract class that all agents inherit from. 
- **Why**: It standardizes how agents run and automatically handles calculating execution latency, formatting inputs/outputs, and logging the `AgentTrace` directly to Firestore. This guarantees that **every decision made by the system is transparent and visible to the end user**.

### C. The Orchestrator (`backend/agents/orchestrator.py`)
The central nervous system of the backend. It receives a `NormalizedSignal`, fetches active incidents from the database, and orchestrates the first three agents in the pipeline.

### D. The Agents

#### 1. Signal Fusion Agent (`backend/agents/signal_fusion.py`)
- **Type**: Rule-based (Deterministic).
- **Logic**: Uses the Haversine formula (`utils/geospatial.py`) to calculate the physical distance between a new signal and active incidents. If the signal is within 1.5km of an incident, it merges it. Otherwise, it spawns a new cluster candidate.

#### 2. Credibility Agent (`backend/agents/credibility.py`)
- **Type**: Rule-based (Deterministic).
- **Logic**: Analyzes all signals within the current `IncidentContext`. If it detects that signals are hinting at completely different crisis types (e.g., one claims "fire", another claims "flooding"), it flags a contradiction and penalizes the overall confidence score. 

#### 3. Classification Agent (`backend/agents/classification.py`)
- **Type**: LLM-driven (Google Gemini 1.5 Flash).
- **Logic**: It ingests the `IncidentContext` and `CredibilityReport` and uses Gemini to output a strict JSON classification (Type, Severity 1-5, Confidence, and Reasoning). 
- **Resilience Feature**: Contains a `_rule_based_fallback` method. If the Google AI Studio API key is missing or the external API goes down, this agent gracefully falls back to a deterministic classification rule, preventing system crashes during live demos.

### Day 1 & Day 2 Testing
A test script was created at `backend/test_pipeline.py` to validate the end-to-end flow.
- **Result**: PASS. The orchestrator successfully generated a new cluster, ran it through credibility scoring, and gracefully utilized the rule-based fallback when the LLM was intentionally disabled.

---

## 3. Implemented Components (Day 3: Resource & Comms Extension)

Day 3 built upon the active classification pipeline, kicking in once an incident is marked as `active` (confidence >= 0.6).

### A. Mock Sensor Stream (`backend/services/mock_sensor_stream.py`)
Implemented a mock IoT sensor stream that simulates critical parameter breaches (like water level thresholds or extreme temperatures). These signals are highly credible and immediately trigger the orchestration pipeline.

### B. The Agents

#### 1. Resource Allocation Agent (`backend/agents/resource_allocation.py`)
- **Type**: Rule-based (Deterministic).
- **Logic**: Sorts all active crises globally based on a weighted priority formula (`severity * 0.35 + confidence * 0.20 + population * 0.25`). It then allocates available resources (ambulances, police units, etc.) down the priority list. If a lower-priority incident requests a resource that was depleted by a higher-priority one, it logs a `ConflictDetails` explaining the deficit.

#### 2. Simulation Agent (`backend/agents/simulation.py`)
- **Type**: Rule-based (Deterministic Templates).
- **Logic**: Takes the `AllocationResult` and computes "before and after" states using predefined `ACTION_TEMPLATES`. For example, deploying rescue teams improves `coverage_pct` and `response_time_improvement_min`.

#### 3. Stakeholder Messaging Agent (`backend/agents/stakeholder_messaging.py`)
- **Type**: LLM-driven (Google Gemini 1.5 Flash).
- **Logic**: Uses the LLM to draft exactly 3 tailored alerts based on the incident severity and allocated resources: `public_alert`, `hospital_alert`, and `media_brief`.
- **Resilience Feature**: Contains a `_rule_based_fallback` method for reliable offline/keyless execution.

### Day 3 Testing (Multi-Crisis Allocation)
A test script (`backend/test_day3.py`) was used to validate multi-crisis functionality. Two concurrent mock sensor breaches were fired (Flooding and Heatwave). 
- **Result**: PASS. The Orchestrator correctly processed both in parallel, generated priority scores, accurately split the mock resource state without crashing, and generated a total of 18 agent traces.

---

## 4. Implemented Components (Day 4: Recovery & Error Correction)

Day 4 focused on correcting pipeline assumptions. If the system is tricked into firing an alert, we need a way to gracefully detect the contradiction and roll it back.

### A. False Alarm Trigger (`backend/api/demo.py`)
We added a specific API endpoint (`POST /demo/false-alarm/{incident_id}`).
- **Logic**: Generates a synthetic `field_report` signal claiming the area is clear and there is no crisis. Field reports are hardcoded to have a `0.99` credibility score.

### B. The Agent

#### 1. Recovery Agent (`backend/agents/recovery.py`)
- **Type**: Rule-based (Deterministic).
- **Contradiction Detection**: If a new signal enters the pipeline and matches an existing incident, the Orchestrator pauses the normal Day 3 pipeline and instead routes it to the `RecoveryAgent`.
- **Alert Retraction Flow**: The agent checks if the new signal is a highly credible field report that explicitly contradicts the existing classification. If so, it outputs a `RETRACT` action with a tailored retraction message.
- **Degraded Mode**: If the overall incident confidence has slipped below `0.5` due to poor quality signals, the agent outputs an `ESCALATE` action to flag the incident for manual human verification.

### C. Orchestrator Integration
The `Orchestrator` was updated to intercept the `RETRACT` command. If received, it instantly changes the incident status to `false_alarm`, moves the pipeline stage to `resolved`, pushes a WebSocket update, and immediately halts the rest of the pipeline to prevent further resource deployment.

### Day 4 Testing (Recovery & Retraction)
A test script (`backend/test_day4.py`) was written to test the rollback flow.
1. We triggered a major flooding crisis.
2. We verified the Orchestrator assigned it an `active` status.
3. We injected the False Alarm field report targeting the same incident.
- **Result**: PASS. The Orchestrator intercepted the update, the `RecoveryAgent` successfully identified the contradiction, issued a `RETRACTED` decision, and cleanly updated the incident to `false_alarm`.

---

## 5. Live Integration & Firebase Pipeline (Day 5)

We integrated the entire system and created a dedicated runner script to push live data directly to the Firebase project (`ciro-61389`).

### A. Live Pipeline Runner (`backend/run_live_integration.py`)
This script acts as the ultimate end-to-end integration test.
- **Ingestion**: It attempts to fetch live weather data via OpenWeather API. If the API fails (e.g., due to an invalid key), it automatically falls back to generating a synthetic critical sensor breach.
- **Normalization & Storage**: The signal is parsed into a `NormalizedSignal` and pushed directly to the live Firestore `signals` collection.
- **Orchestration**: It triggers the full Antigravity pipeline, executing all 7 agents in sequence: `SignalFusionAgent` ➔ `CredibilityAgent` ➔ `RecoveryAgent` ➔ `ClassificationAgent` ➔ `ResourceAllocationAgent` ➔ `SimulationAgent` ➔ `StakeholderMessagingAgent`.
- **Firebase Verification**: At the end of the run, the script fetches the final state directly from Firebase, proving that the `Incident` and all `AgentTrace` logs were successfully written to the cloud.

### Day 5 Testing (Live Firebase Integration)
The `run_live_integration.py` script was executed locally against the live `ciro-61389` Firebase project.
- **Result**: PASS. The system gracefully handled the live weather API failure by falling back to the synthetic signal, pushed the signal through the 7-agent pipeline, and successfully wrote the resulting `Incident` and 8 discrete `AgentTrace` logs to Firestore. No in-memory fallbacks were needed.

---

## 6. Setup & Running the System

### Prerequisites
1. Python 3.10+
2. A Google AI Studio API Key. 

### Environment Setup (`backend/.env`)
Create a `.env` file in the `backend` directory with the following minimum required variables:
```env
ENVIRONMENT="development"
GEMINI_API_KEY="your_google_ai_studio_api_key"
```

### Running the API
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
fastapi dev main.py
```
