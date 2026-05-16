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
├── agents/                     # The old core intelligence. The AI "Assembly Line". (Deprecated)
│
├── graph/                      # The LangGraph Orchestration Layer (The new Brains).
│   ├── orchestrator.py         # The compiled StateGraph and execution engine.
│   ├── state.py                # TypedDict defining the IncidentState schema.
│   ├── edges.py                # Conditional routing logic between nodes.
│   └── nodes/                  # Single-responsibility AI nodes.
│       ├── fusion.py           # Groups reports by physical location.
│       ├── credibility.py      # Detects contradictions in the reports.
│       ├── classification.py   # Uses an LLM to categorize the crisis type & severity.
│       ├── allocation.py       # Prioritizes crises and dispatches ambulances/police.
│       ├── simulation.py       # Calculates projected response times.
│       ├── messaging.py        # Drafts public alerts and media briefs.
│       └── recovery.py         # Detects false alarms and issues retractions.
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

CIRO utilizes a **LangGraph-driven State Machine Architecture**. 

Instead of a rigid linear pipeline where agents directly call each other, CIRO uses a centralized `IncidentState`. Nodes (stateless functions) read from this state, perform specialized tasks, and return state updates. The graph's edges conditionally route the state to the next node or halt execution based on the results.

### The Data Flow Lifecycle
1. **Ingestion:** An external system sends a JSON payload to `POST /signals/ingest`.
2. **Normalization:** The `signal_normalizer.py` cleans the text and formats it into a standardized `NormalizedSignal`.
3. **Graph Invocation:** The signal is injected into the initial `IncidentState`, and the LangGraph `orchestrator_graph.ainvoke()` is called.
4. **Node 1 (Signal Fusion):** Checks the GPS coordinates. If the signal is within 1.5km of an active crisis, it attaches it to that crisis. Otherwise, it creates a new "Incident Context".
5. **Node 2 (Credibility):** Looks at all the signals in the cluster. Are they contradicting each other? Returns a `CredibilityReport` to the state.
6. **Node 3 (Recovery):** Checks if the signal is a highly credible field report saying "false alarm!". If so, it issues a `RETRACT` action.
7. **Conditional Edge:** If retracted, the graph routes to `END`. Otherwise, it routes to `Classification`.
8. **Node 4 (Classification):** Hands the data to Google Gemini to officially classify the severity (1-5) and exact crisis type.
9. **Conditional Edge:** If confidence is too low, the graph could route to a human-review node. Otherwise, it routes to `Allocation`.
10. **Node 5 (Allocation):** Looks at the global pool of emergency units, prioritizes this crisis, and dispatches units.
11. **Node 6 (Simulation):** Calculates how much these dispatched units will help the situation.
12. **Node 7 (Messaging):** Hands the finalized data back to Gemini to draft targeted text alerts.
13. **Completion:** The graph reaches the `END` node, yielding the final processed state.

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

### 📂 The `graph/` Directory (The LangGraph Engine)

#### `state.py`
* **Purpose:** The single source of truth for the entire pipeline.
* **Key Components:** `IncidentState` (a `TypedDict`). It defines all fields (like `context`, `classification`, `errors`). It uses `Annotated` reducers (like `operator.add`) to safely append logs and errors without overwriting previous data.

#### `orchestrator.py`
* **Purpose:** The traffic cop and state machine compiler.
* **Key Components:** Uses `StateGraph` from LangGraph. It registers all nodes, defines the standard edges (Node A -> Node B), and sets up conditional edges (like `route_after_recovery`). It exposes the compiled `orchestrator_graph`.

#### `edges.py`
* **Purpose:** Routing logic.
* **Key Functions:** Functions like `route_after_recovery` read the current state and return a string (e.g., `"END"` or `"CONTINUE"`) telling LangGraph where to route next.

#### 📂 `nodes/` (The Single-Responsibility Agents)
* **Purpose:** Stateless functions that receive the `IncidentState`, perform specialized AI or rule-based logic, and return a dictionary of state updates.
* **Key Files:** 
  * `fusion.py`: Geospatial clustering.
  * `credibility.py`: Contradiction detection.
  * `recovery.py`: Protects the system from false alarms.
  * `classification.py`: Identifies the crisis using Gemini 1.5 Flash. Includes graceful fallback if the LLM fails.
  * `allocation.py`: Dispatches emergency units.
  * `simulation.py`: Estimates impact.
  * `messaging.py`: Drafts PR and public alerts.

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
