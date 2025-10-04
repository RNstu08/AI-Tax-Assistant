-----

# AI Tax Assistant - A Multi-Agent System for Personalized Tax Declarations

_A modular, auditable, and transparent conversational AI designed to assist German employees with their tax deductions, featuring receipt processing, consent management, a full reasoning trace, and built-in audit capabilities._

---

## 🎯 The Challenge & Project Goals

The core task, as defined by the case study was to design and prototype a personalized, intelligent, and transparent multi-agent system for tax declarations.

This project aims to fulfill that challenge by delivering:
-   **Personalized Stepwise Guidance:** For German employee tax deductions for the 2024/2025 tax years.
-   **Explainable, Multi-Agent Reasoning:** Allowing users to see all agent steps, memory usage, rule citations, and calculations.
-   **Receipts and Audit:** Enabling users to upload files, extract data via OCR, and manage their data with GDPR-compliant retention policies, a full audit trail, and an undo function.
-   **Business-Level Safety:** Ensuring all changes, evidence, and settings are logged and auditable for compliance.
-   **Intuitive and Accessible UX:** Featuring new-user hints, proactive suggestions, and clear action-oriented controls to suggest and execute specific actions (like saving data) with user confirmation.

---

## 🏛️ Architectural Overview: An Agentic Pipeline Approach

The system is designed as an **agentic pipeline**, where a user's request flows through a "team" of specialized agents (nodes). Each agent has a specific job, enriching a central data object (`TurnState`) as it passes through the system. This modular, graph-based design is managed by an **Orchestrator** and ensures clarity, testability, and scalability.

### End-to-End Flow

```text
                 ┌──────────────────────────────────┐
User Input ──────►│           Orchestrator           │
                 │ ┌─────────────┬──────────────┐   │
                 │ │ Safety Gate │    Router    │   │
                 │ └──────┬──────┴───────┬──────┘   │
                 │        │              │          │
                 │ ┌──────▼──────┬───────▼──────┐   │
                 │ │  Extractor  │ Knowledge    │   │
                 │ │(Finds facts)│ Agent (Finds │   │
                 │ └──────┬──────┘   rules)    │   │
                 │        │              │          │
                 │ ┌──────▼──────┬───────▼──────┐   │
                 │ │ Question    │  Calculators │   │
                 │ │ Generator   │ (Does math)  │   │
                 │ └──────┬──────┴───────┬──────┘   │
                 │        │              │          │
                 │ ┌──────▼──────────────▼──────┐   │
                 │ │          Reasoner          │   │
                 │ │      (Synthesizes Answer)    │   │
                 │ └─────────────┬──────────────┘   │
                 │               │                   │
                 │ ┌─────────────▼──────────────┐   │
                 │ │    Critic & Action Planner │   │
                 │ └─────────────┬──────────────┘   │
                 └───────────────│──────────────────┘
                                 │
                                 ▼
                     UI (Answer & Actions)
````

-----

## 🖥️ Usage Guide

**1. Chat**: Start a conversation by asking about your deductions (e.g., *"I commute 20km for 200 days in 2024"* or *"I worked from home 80 days this year."*). The AI agents will parse, reason, calculate, and cite the relevant tax rules.

**2. Actions**: After you provide information, the assistant will propose to save it. Go to the **Actions** tab to **✅ Confirm** the change. No data is saved without your consent. You can also **⏪ Undo** your last confirmed action.

**3. Receipts**: Upload a receipt (PDF/JPG/PNG) in the **Receipts** tab. Run **OCR** (with consent) to extract text. If the AI detects a deductible item (like a laptop), it will proactively ask if you want to import it.

**4. Profile & Audit**: The **Profile** tab shows all your saved deductions at a glance. The **Audit** tab provides a detailed, timestamped log of every single action taken—from profile updates to file uploads and settings changes.

**5. Summary & Export**: The **Summary** tab shows a table of your calculated deductions. From here, you can download a professional **PDF** or a machine-readable **JSON** report.

**6. Settings**: Configure the assistant's language, your data retention policies, and manage consent for features like OCR. You can also download your user data in compliance with GDPR.

-----

## ✨ Key Features vs. Case Study Requirements

| Requirement                 | How It's Implemented                                                                                                                                                             |
| --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Memory Integration** | **`ProfileStore`** (`app/memory/store.py`) provides persistent SQLite-backed long-term memory. The **Profile** and **Audit** tabs visibly show its state.                             |
| **Personalised Guidance** | **`InMemoryRetriever`** (`app/knowledge/retriever.py`) grounds all responses in the YAML rulebook. The **`Reasoner`** agent crafts answers based on user profile data and retrieved rules. |
| **Action-Oriented** | **`ActionPlanner`** (`app/orchestrator/graph.py`) proposes changes, which appear in the **Actions** tab for explicit user confirmation before being committed to the `ProfileStore`. |
| **Streaming Responses** | The **`GroqAdapter`** streams LLM tokens directly to the Streamlit UI for a real-time, typewriter effect in the chat.                                                             |
| **Transparent Reasoning** | The **Trace** tab provides a step-by-step visualization of the agent pipeline, showing which agents ran and which tax rules were used for each query.                             |
| **Memory's Impact Shown** | Demonstrated through pronoun resolution ("another one") and by the system using saved profile data in subsequent conversations (e.g., "what's my summary?").                  |
| **Adaptive Interaction** | The assistant adapts its language based on user **Settings** and avoids re-asking for information already present in the user's profile.                                         |

-----

## 🤝 Edge Cases & Guardrails

  - **Out of Scope**: The `Safety Gate` agent provides a friendly message when asked about unsupported topics (e.g., Austrian tax law, freelancer status).
  - **Clarification, Not Hallucination**: If information is missing, the `Question Generator` agent asks for it explicitly rather than inventing facts.
  - **Consent Enforcement**: OCR processing is blocked until the user grants permission in the **Settings** tab, ensuring privacy compliance.
  - **File Safety**: The system validates all uploads for allowed types (`PDF`, `JPG`, `PNG`) and size (\<7MB), and sanitizes filenames to prevent malicious inputs.
  - **Data Integrity**: All stored files and evidence logs are hashed. The **Maintenance** tab includes an "Integrity Scan" to verify that no data has been tampered with.

-----

## 🚀 Setup & Running the Prototype

**Prerequisites:** Python 3.11+. Tesseract OCR Engine is optional but required for the receipt scanning feature.

**1. Clone the Repository**

```bash
git clone [https://github.com/RNstu08/AI-Tax-Assistant.git](https://github.com/RNstu08/AI-Tax-Assistant.git)
cd AI-Tax-Assistant
```

**2. Create and Activate Virtual Environment**

```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

**3. Install Dependencies**
This command installs the project in editable mode along with all development dependencies.

```bash
pip install -e .
pip install -r requirements-dev.txt
# For OCR capabilities (optional, requires Tesseract installation)
pip install -r requirements-ocr.txt
```

**4. Set Up API Keys**
Create a `.env` file from the example:

```bash
cp .env.example .env
```

Then, add your Groq API key or any other providers API key to the `.env` file:

```ini
GROQ_API_KEY="your_groq_api_key_here"
```

**5. Run the Application**
The application will be available at `http://localhost:8501`.

```bash
# Windows:
scripts/run.ps1

# Or (all platforms):
streamlit run app/ui/streamlit_app.py
```

-----

## 📂 Project Structure

```
AI-Tax-Assistant/
├── .data/                  # Stores persistent data (DB, indexes, uploads)
├── app/
│   ├── i18n/               # Internationalization and microcopy
│   ├── infra/              # Configuration and settings
│   ├── knowledge/          # Knowledge base ingestion and retrieval
│   ├── llm/                # LLM adapter (Groq)
│   ├── maintenance/        # Data retention and integrity scanning tools
│   ├── memory/             # Long-term memory (SQLite ProfileStore)
│   ├── nlu/                # NLU helpers (quantity parsing, context)
│   ├── ocr/                # OCR adapters and runner
│   ├── orchestrator/       # The core agentic graph and state model
│   ├── receipts/           # Receipt parsing logic
│   ├── reports/            # PDF and JSON export generation
│   ├── safety/             # File validation and safety policies
│   ├── services/           # Utility services (e.g., logging)
│   └── ui/                 # Streamlit UI components and main app
├── knowledge/
│   └── rules/de/           # The ground-truth YAML tax rule files
├── scripts/                # Helper scripts for setup and running
├── tests/                  # Unit, integration, and E2E tests
├── tools/                  # Deterministic calculators and money helpers
└── .github/                # CI workflow for linting, type-checking, and testing
```
-----

## 💡 Reflection & Future Improvements

  * **Challenges:** The primary challenge was ensuring the system remained factually grounded. This was solved by adopting a strict **retriever-first architecture** where the LLM's role is to *synthesize* provided information, not to generate it.
  * **Future Work:**
      * **Advanced NLU:** Integrate a proper NER model (e.g., using spaCy) for more robust extraction.
      * **Hybrid Retriever:** Combine the current keyword search with vector-based semantic search for better rule matching.
      * **Production-Ready Memory:** Replace SQLite with a more scalable database like PostgreSQL.
      * **User Authentication:** Implement a full authentication system to replace the current single "demo" user.

-----

## 🛠️ Tech Stack

  - **Python (3.11+)**
  - **Orchestration:** Custom Graph-Based Agentic System
  - **LLMs:** Groq API (Llama 3.1)
  - **UI:** Streamlit
  - **Memory:** SQLite
  - **Document Processing:** Tesseract, PyMuPDF, Pillow
  - **Code Quality:** Ruff, Black, Mypy, Pytest, Pre-commit
  - **CI/CD:** GitHub Actions

-----

## 🧪 Testing & CI

The project is configured with a professional-grade testing and CI pipeline.

  - **Run all tests locally:**
    ```bash
    pytest -q
    ```
  - **CI:** The workflow in `.github/workflows/ci.yml` automatically runs linting (Ruff), formatting checks (Black), type checks (Mypy), and the full Pytest suite on every push and pull request.

<!-- end list -->

```
```
