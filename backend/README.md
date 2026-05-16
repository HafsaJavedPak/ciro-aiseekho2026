# CIRO Backend: System Architecture and Codebase Guide

Welcome to the **CIRO (Crisis Intelligence & Response Orchestrator)** backend repository! If you are a new developer joining the team, this guide is designed to be your compass. It breaks down exactly how the system works, where every file lives, and how they all connect together.

---

## 1. High-Level Overview & Purpose

### What is CIRO?
When a crisis occurs (like a flood or a massive fire), emergency services are often overwhelmed by chaotic, noisy data from social media, sensors, and 911 calls. 

**CIRO** is an AI-driven backend subsystem designed to cut through that noise. It ingests raw data, filters out the junk, intelligently clusters related reports together, verifies their credibility, categorizes the crisis, allocates emergency resources, and drafts stakeholder alerts—all in seconds.

### The Core Problem It Solves
Instead of forcing a single, giant AI model to "solve the crisis" (which is slow, expensive, and prone to hallucinations), CIRO uses a **Multi-Agent Orchestration Pattern**. It breaks the problem down into tiny, specialized AI "agents" that pass data to each other in a strict assembly line.

---

## 2. Project Hierarchy & Directory Structure

Here is a bird's-eye view of the backend folder. 

```text
backend/
├── main.py                     # The FastAPI application entry point.
├── config.py                   # Loads environment variables (API keys, DB settings).
├── requirements.txt            # Python dependencies.
├── run_live_integration.py     # CLI script to run a full end-to-end live data test.
├── firebase-credentials.json   # Google Cloud / Firebase service account key.
├── test_*.py                   # Various test scripts (test_pipeline.py, test_day3.py, etc.)
│
├── agents/                     # The core intelligence. The AI "Assembly Line".
│   ├── base.py                 # The parent class ensuring every agent logs its decisions.
│   ├── orchestrator.py         # The manager that passes data between the agents.
│   ├── signal_fusion.py        # Groups reports by physical location.
│   ├── credibility.py          # Detects contradictions in the reports.
│   ├── classification.py       # Uses an LLM to categorize the crisis type & severity.
│   ├── resource_allocation.py  # Prioritizes crises and dispatches ambulances/police.
│   ├── simulation.py           # Calculates projected response times.
│   ├── stakeholder_messaging.py# Drafts public alerts and media briefs.
│   └── recovery.py             # Detects false alarms and issues retractions.
│
├── api/                        # FastAPI endpoints (The doors into the system).
│   ├── demo.py                 # Endpoints to trigger scripted hackathon demos.
│   ├── incidents.py            # Endpoints to fetch active crises.
│   └── signals.py              # The main ingestion endpoint for raw data.
│
├── models/                     # Pydantic schemas (Strict data contracts).
│   ├── agent_io.py             # Data passed *between* agents.
│   ├── allocation.py           # Data structure for resource dispatching.
│   ├── incident.py             # Data structure for a full crisis event.
│   ├── signal.py               # Data structure for raw incoming data.
│   ├── simulation.py           # Data structure for before/after states.
│   └── trace.py                # Data structure for AI audit logs.
│
├── services/                   # External connections (Databases, APIs, WebSockets).
│   ├── firestore_service.py    # Reads/writes to Google Firebase.
│   ├── websocket_manager.py    # Pushes live updates to the frontend UI.
│   ├── weather_service.py      # Fetches live weather from OpenWeatherMap.
│   ├── mock_sensor_stream.py   # Simulates IoT sensor breaches.
│   └── mock_social_stream.py   # Simulates Twitter/X data feeds.
│
├── utils/                      # Helper functions.
│   ├── geospatial.py           # Math for calculating distances between GPS points.
│   └── signal_normalizer.py    # Cleans and scores raw text data.
│
└── data/                       # Static JSON files for mock scenarios.
```

---

## 3. System Architecture & Data Flow

CIRO utilizes a **Sequential Agentic Pipeline Architecture**. 

Think of it like a factory conveyor belt. Raw materials (data) enter at the start, and at each station, a specialized worker (an agent) inspects the item, adds value to it, and passes it to the next worker. 

### The Data Flow Lifecycle
1. **Ingestion:** An external system sends a JSON payload to `POST /signals/ingest`.
2. **Normalization:** The `signal_normalizer.py` cleans the text, extracts keywords, and formats it into a standardized `NormalizedSignal`.
3. **Orchestration Kickoff:** The `api/signals.py` endpoint adds the signal to a background task, calling `Orchestrator.process_signal()`.
4. **Agent 1 (Signal Fusion):** Checks the GPS coordinates. If the signal is within 1.5km of an active crisis, it attaches it to that crisis. Otherwise, it creates a new "Incident Context".
5. **Agent 2 (Recovery):** Checks if this new signal is actually a highly credible field report saying "false alarm!". If so, it retracts the crisis and stops the pipeline.
6. **Agent 3 (Credibility):** Looks at all the signals in the cluster. Are they contradicting each other? (e.g., One says "Flood", another says "Fire"). If yes, it lowers the confidence score.
7. **Agent 4 (Classification):** Hands the data to Google Gemini to officially classify the severity (1-5) and exact crisis type.
8. **Agent 5 (Resource Allocation):** Looks at the global pool of ambulances and police cars, prioritizes this crisis against all others, and dispatches units.
9. **Agent 6 (Simulation):** Calculates how much these dispatched units will help the situation.
10. **Agent 7 (Messaging):** Hands the finalized data back to Gemini to draft targeted text alerts.
11. **Persistence:** The `Orchestrator` saves the final `Incident` and all the `AgentTrace` logs (the audit trail of every agent's thought process) to Firebase.
12. **Broadcast:** The `Orchestrator` pushes the updated data through WebSockets so the frontend UI updates instantly without refreshing.

---

## 4. Detailed File-by-File Breakdown

### `main.py`
* **Purpose:** The entry point for the FastAPI server.
* **Key Components:** `app = FastAPI()` initializes the server. It includes routers from the `api/` directory and mounts the WebSocket endpoint `/ws`.

### `config.py`
* **Purpose:** Centralized configuration management.
* **Key Classes:** `Settings` class loads variables from `.env` (like `GEMINI_API_KEY` and `FIREBASE_PROJECT_ID`).

---

### 📂 The `models/` Directory (Data Contracts)
*These files contain no logic. They use Pydantic to ensure data is strictly typed so agents don't crash from unexpected inputs.*

* **`signal.py`**: Defines `RawSignal` (what comes in) and `NormalizedSignal` (the cleaned version).
* **`incident.py`**: Defines `Incident` (the overarching crisis) and `CrisisClassification` (the LLM output).
* **`trace.py`**: Defines `AgentTrace` (the audit log tracking exactly how fast an agent ran and what decision it made).
* **`agent_io.py`**: Defines `IncidentContext` (a group of signals) and `CredibilityReport` (contradiction flags).
* **`allocation.py`**: Defines `AllocationResult` and `ConflictDetails` (when resources run out).
* **`simulation.py`**: Defines `SimulationResult` (before/after states).

---

### 📂 The `agents/` Directory (The Brains)

#### `base.py`
* **Purpose:** The foundational blueprint for every AI agent.
* **Key Classes:** `BaseAgent`. It provides the `run()` wrapper method.
* **Flow:** Every time an agent's `run()` method is called, the BaseAgent starts a timer, executes the specific agent logic, stops the timer, formats the input/output, and pushes an `AgentTrace` to Firebase.

#### `orchestrator.py`
* **Purpose:** The traffic cop. It manages the execution sequence of all agents.
* **Key Functions:** `process_signal(signal)`. It takes a signal, fetches active incidents from the database, and awaits the response of each agent sequentially, piping the output of one agent into the input of the next.

#### `signal_fusion.py`
* **Purpose:** Geospatial clustering.
* **Key Functions:** `execute()`. Input: a signal and active incidents. Uses distance math to return an `IncidentContext`.

#### `credibility.py`
* **Purpose:** Contradiction detection.
* **Key Functions:** `execute()`. Input: `IncidentContext`. Iterates through signals and returns a `CredibilityReport` flagging if multiple crisis types are reported simultaneously.

#### `classification.py`
* **Purpose:** Identifies the crisis using Gemini 1.5 Flash.
* **Key Functions:** `execute()`. Takes the context and credibility report, prompts the LLM to output JSON. Includes a `_rule_based_fallback` method if the API fails. Returns a `CrisisClassification`.

#### `resource_allocation.py`
* **Purpose:** Dispatches emergency units.
* **Key Functions:** `execute()`. Sorts all crises by a weighted formula (`severity * 0.35 + confidence * 0.20 + population * 0.25`). Deducts required resources from the global state. Returns an `AllocationResult`.

#### `simulation.py`
* **Purpose:** Estimates impact.
* **Key Functions:** `execute()`. Applies hardcoded templates based on dispatched resources to return a `SimulationResult` (e.g., estimating response time improvements).

#### `stakeholder_messaging.py`
* **Purpose:** Drafts PR and public alerts.
* **Key Functions:** `execute()`. Prompts Gemini to write a public alert, a hospital alert, and a media brief. Returns a dictionary of strings.

#### `recovery.py`
* **Purpose:** Protects the system from false alarms.
* **Key Functions:** `execute()`. Checks if a new highly-credible signal contradicts the crisis. Returns an action: `CONFIRM`, `RETRACT`, or `ESCALATE`.

---

### 📂 The `api/` Directory (The Endpoints)

#### `signals.py`
* **Purpose:** Receives data.
* **Key Functions:** `ingest_signal()`. Accepts a `RawSignal`, normalizes it, and offloads the heavy lifting to the orchestrator via FastAPI `BackgroundTasks`.

#### `incidents.py`
* **Purpose:** Exposes data to the frontend.
* **Key Functions:** Endpoints to fetch active incidents and historical trace logs from Firestore.

#### `demo.py`
* **Purpose:** Hackathon presentation controls.
* **Key Functions:** `trigger_demo_scenario()` starts a mocked stream of social media posts. `trigger_false_alarm()` injects a fake field report to force the Recovery Agent to fire.

---

### 📂 The `services/` Directory (External Connections)

#### `firestore_service.py`
* **Purpose:** Database abstraction layer.
* **Key Functions:** Contains methods like `save_incident()`, `save_trace()`, and `get_active_incidents()`. **Crucial Detail:** It attempts to connect to Firebase. If credentials fail or are missing, it silently falls back to an in-memory dictionary, allowing developers to test locally without an internet connection.

#### `websocket_manager.py`
* **Purpose:** Real-time push notifications.
* **Key Functions:** `broadcast()`. Sends JSON data to all connected frontend clients the millisecond a database record changes.

#### `weather_service.py`, `mock_social_stream.py`, `mock_sensor_stream.py`
* **Purpose:** Data generation. They either fetch real data (OpenWeather) or read from static JSON files in `backend/data/` to simulate crises.

---

### 📂 The `utils/` Directory (Helpers)

#### `signal_normalizer.py`
* **Purpose:** Pre-processing text.
* **Key Functions:** `normalize_signal()`. Extracts keywords from messy text strings and calculates a baseline urgency score.

#### `geospatial.py`
* **Purpose:** Map math.
* **Key Functions:** `haversine_km()`. Calculates the distance in kilometers between two GPS coordinates to determine if two reports are talking about the same physical event.

---

## 5. How It All Fits Together (The Integration Layer)

If you want to see the entire system fire at once, look at **`backend/run_live_integration.py`**.

This is the ultimate "glue" file. It is a standalone CLI script that bypasses the FastAPI server completely to prove the backend works. 
1. It initializes the `firestore_service`.
2. It calls `weather_service` to fetch real weather data.
3. It passes that data directly into `orchestrator.process_signal()`.
4. The Orchestrator manages the hand-offs between all 7 agent files sequentially.
5. The `BaseAgent` class silently catches the inputs and outputs of every step, formatting them into traces.
6. The Orchestrator finishes and saves the final product to Firebase via `firestore_service`.

### Initialization Process:
When you run `fastapi dev main.py`, the system initializes in this order:
1. `config.py` loads the `.env` variables.
2. `firestore_service.py` is instantiated as a singleton (connecting to Firebase or falling back to memory).
3. `orchestrator.py` is instantiated as a singleton, importing and initializing all agent classes.
4. `main.py` binds the routers.
The system then sits idle, waiting for a POST request to hit `/signals/ingest`. When it does, the pipeline roars to life. 

Welcome to the team!
