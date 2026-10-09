# Designing an AI-Powered Intelligent Document Comparison and Change Analysis System Using AI and Software Design Patterns

An enterprise-grade, end-to-end web application that compares baseline (old) and revised (new) documents (PDF, DOCX, TXT), detects structural differences, determines whether underlying semantic meaning has changed, categorizes each modification, evaluates real-world practical impact, and generates an audit-ready PDF comparison report.

---

## 1. Architectural Highlights & Software Design Patterns

The system adheres strictly to classical object-oriented software design patterns and modular clean architecture:

```
                                      [User Request: Upload Old & New Docs]
                                                       │
                                                       ▼
                                         ┌───────────────────────────┐
                                         │ Document Validation Layer │
                                         └─────────────┬─────────────┘
                                                       │
                                                       ▼
                                         ┌───────────────────────────┐
                                         │   FACTORY PATTERN         │
                                         │ (DocumentProcessorFactory)│
                                         └─────────────┬─────────────┘
                                                       │
                           ┌───────────────────────────┼───────────────────────────┐
                           ▼                           ▼                           ▼
                     [PDFAdapter]                [DOCXAdapter]               [TXTAdapter]
                 (ADAPTER PATTERN)           (ADAPTER PATTERN)           (ADAPTER PATTERN)
                 - pypdf extraction          - python-docx               - multi-encoding
                 - OCR image fallback        - paragraph & tables        - clean text
                           │                           │                           │
                           └───────────────────────────┼───────────────────────────┘
                                                       │
                                                       ▼
                                         ┌───────────────────────────┐
                                         │ Preprocessor & Structuring│
                                         │  (StructuredDocument)     │
                                         └─────────────┬─────────────┘
                                                       │
                                                       ▼
                                         ┌───────────────────────────┐
                                         │ Document Section Matcher  │
                                         │  (ADDED / DELETED / MOD)  │
                                         └─────────────┬─────────────┘
                                                       │
                                                       ▼
                                         ┌───────────────────────────┐
                                         │    STRATEGY PATTERN       │
                                         │   (ComparisonService)     │
                                         └─────────────┬─────────────┘
                                                       │
                           ┌───────────────────────────┴───────────────────────────┐
                           ▼                                                       ▼
             ┌───────────────────────────┐                           ┌───────────────────────────┐
             │   TextComparisonStrategy  │                           │ SemanticComparisonStrategy│
             │   - Fast lexical diff     │                           │   - Vector RAG Context    │
             │   - Deterministic rule    │                           │   - Prompt Chaining AI    │
             └───────────────────────────┘                           └─────────────┬─────────────┘
                                                                                   │
                                                                                   ▼
                                                                     ┌───────────────────────────┐
                                                                     │   Prompt Chaining Chain   │
                                                                     │ 1. Difference Analysis    │
                                                                     │ 2. Semantic Equivalence   │
                                                                     │ 3. Category & Importance  │
                                                                     │ 4. Grounded Impact & Conf │
                                                                     └─────────────┬─────────────┘
                                                                                   │
                                                                                   ▼
                                                                     ┌───────────────────────────┐
                                                                     │    Results & PDF Report   │
                                                                     │   (ReportLab Generator)   │
                                                                     └───────────────────────────┘
```

### Factory Pattern (`app.document_processing.factory`)
- **`DocumentProcessorFactory`**: Decouples the upload API from concrete format processors. Inspects the file extension (`.pdf`, `.docx`, `.txt`) and dynamically instantiates the correct adapter conforming to `DocumentAdapterInterface`.

### Adapter Pattern (`app.document_processing.adapters`)
- **`DocumentAdapterInterface`**: Common target interface declaring `extract(file_bytes, filename) -> Tuple[str, dict]`.
- **`PDFAdapter`**: Adapts `pypdf` extraction and incorporates an OCR fallback pipeline for image-only or scanned PDFs.
- **`DOCXAdapter`**: Adapts Microsoft Word `.docx` documents using `python-docx`, extracting paragraph sequences and tabular data.
- **`TXTAdapter`**: Adapts plain text files with automatic multi-encoding fallback (`utf-8`, `utf-8-sig`, `cp1252`, `latin-1`).

### Strategy Pattern (`app.comparison.strategies`)
- **`ComparisonStrategy`**: Abstract algorithm interface declaring `compare(matches, old_doc, new_doc) -> List[ChangeResult]`.
- **`TextComparisonStrategy`**: High-speed lexical, token-level, and rule-based diff strategy without external LLM dependencies.
- **`SemanticComparisonStrategy`**: Deep semantic strategy orchestrating local Vector RAG and multi-stage Prompt Chaining to discern true meaning shifts (e.g. 75% to 80% requirement threshold increases) from trivial wording alterations.
- **`ComparisonService`**: Context class allowing dynamic runtime swapping of strategies.

---

## 2. RAG & Prompt Chaining Workflow

### RAG (Retrieval-Augmented Generation) (`app.ai.rag`)
- **Corpus Chunking**: Automatically segments old and new documents into section-aware semantic chunks.
- **Vector Embeddings**: Computes TF-IDF vector embeddings and cosine similarity in-memory using `scikit-learn` and `numpy`.
- **Dual-Version Context Retrieval**: When evaluating any detected change, the retriever extracts the top-$k$ relevant contextual passages from both the original and revised documents, supplying background policies and surrounding provisions to the reasoning engine.

### Prompt Chaining Pipeline (`app.ai.prompts` & `app.ai.prompt_chain`)
The AI evaluation pipeline executes a 4-stage sequential chain of reasoning:
1. **Stage 1 (Difference Understanding)**: Pinpoints the exact text modification within its section context.
2. **Stage 2 (Semantic Equivalence)**: Distinguishes substantive rule changes from stylistic paraphrasing (e.g., *"Students must submit"* vs *"Students are required to submit"* is recognized as `Wording-only Change`).
3. **Stage 3 (Categorization & Importance)**: Assigns precise taxonomy (`Requirement Change`, `Rule Change`, `Number/Value Change`, `Addition`, `Removal`, `Wording-only Change`, `Other`) and assesses severity (`HIGH`, `MEDIUM`, `LOW`).
4. **Stage 4 (Grounded Practical Impact & Confidence)**: Synthesizes operational consequences grounded strictly in document evidence without fabricating external facts, providing a cautious confidence rating (`HIGH`, `MEDIUM`, `LOW`).

---

## 3. Project Structure

```
ai-doc-compare/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes.py              # FastAPI endpoints (/health, /compare, /report/pdf)
│   │   ├── document_processing/       # Member 1 Pipeline
│   │   │   ├── adapters/
│   │   │   │   ├── docx_adapter.py    # DOCX Adapter
│   │   │   │   ├── pdf_adapter.py     # PDF Adapter with OCR fallback
│   │   │   │   └── txt_adapter.py     # TXT Adapter
│   │   │   ├── factory.py             # DocumentProcessorFactory
│   │   │   ├── interfaces.py          # DocumentAdapterInterface
│   │   │   ├── ocr.py                 # OCR engine with graceful handling
│   │   │   ├── preprocessor.py        # Section & paragraph parsing
│   │   │   ├── service.py             # Member 1 Facade
│   │   │   └── validators.py          # Format, size, and corruption checks
│   │   ├── comparison/                # Member 2 Pipeline
│   │   │   ├── strategies/
│   │   │   │   ├── base.py            # ComparisonStrategy ABC
│   │   │   │   ├── text_strategy.py   # TextComparisonStrategy
│   │   │   │   └── semantic_strategy.py # SemanticComparisonStrategy
│   │   │   ├── classifier.py          # Deterministic classifier & rule heuristics
│   │   │   ├── matcher.py             # Paragraph & section matcher
│   │   │   └── service.py             # ComparisonService Context
│   │   ├── ai/
│   │   │   ├── client.py              # LLM client with fallback to deterministic engine
│   │   │   ├── config.py              # Environment variable configurations
│   │   │   ├── prompts.py             # Centralized Prompt Chaining prompts
│   │   │   ├── prompt_chain.py        # Prompt chain execution pipeline
│   │   │   └── rag.py                 # Local Vector RAG retriever
│   │   ├── reporting/
│   │   │   └── pdf_generator.py       # ReportLab PDF report builder
│   │   ├── models/
│   │   │   └── schemas.py             # Pydantic schemas
│   │   └── main.py                    # FastAPI entrypoint with CORS
│   └── tests/                         # 24 Automated Pytest Suite
├── frontend/                          # Vite + React Modern Web Application
│   ├── src/
│   │   ├── App.jsx                    # Two-Screen UI (Upload & Results)
│   │   ├── index.css                  # Professional responsive design system
│   │   └── main.jsx
│   ├── index.html
│   └── vite.config.js
├── data/
│   ├── samples/                       # Sample test files (.pdf, .docx, .txt)
│   ├── uploads/                       # Working upload staging
│   └── reports/                       # Generated audit reports
├── .env.example                       # Environment configuration template
├── .gitignore
├── pytest.ini                         # Pytest configuration
└── README.md
```

---

## 4. Installation & Local Run Instructions

### Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- Node.js 18+ and npm

### 1. Backend Setup

```bash
# Navigate to the project root
cd ai-doc-compare

# Install Python backend dependencies
pip install -r requirements.txt
# Or install directly:
pip install fastapi "uvicorn[standard]" pydantic python-multipart python-docx pypdf reportlab httpx python-dotenv pytest numpy scikit-learn pytesseract
```

### 2. Frontend Setup

```bash
cd frontend
npm install
```

### 3. Environment Configuration

Copy `.env.example` to `.env` in the root or `backend` folder:
```bash
cp .env.example .env
```

*(Note: The system functions completely out of the box even without any external AI API keys, automatically using its built-in semantic analysis engine and vector RAG).*

---

## 5. Running the Application

### Start the Backend (Terminal 1)
```bash
cd ai-doc-compare
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```
- API Health Check: `http://127.0.0.1:8000/api/health`
- Interactive OpenAPI Docs: `http://127.0.0.1:8000/docs`

### Start the Frontend (Terminal 2)
```bash
cd ai-doc-compare/frontend
npm run dev
```
- Open browser at `http://localhost:5173`

---

## 6. Two-Screen UI Walkthrough

### Screen 1: Upload Documents
- **Baseline (Old) & Revised (New) Dropzones**: Clear drop zones accepting PDF, DOCX, and TXT files.
- **Comparison Strategy Selector**: Toggle between *Semantic AI Strategy* (Vector RAG + Prompt Chaining) and *Text Diff Strategy*.
- **Quick Sample Loader**: One-click button to load the canonical Academic Attendance Policy sample (*75% → 80%* threshold change).
- **Interactive Validation**: Validates file types and sizes before submission.

### Screen 2: Comparison Results
- **Summary Metrics**: Real-time counter cards for Total Changes, Added, Deleted, Modified, and High/Medium/Low importance.
- **Strict Requirement Filters**:
  - `All`
  - `Added`
  - `Deleted`
  - `Modified`
  - `High`
  - `Medium`
  - `Low`
- **Side-by-Side Visual Diff**: Previous (Old) text in soft red container and Revised (New) text in soft green container.
- **Structured Findings**: Section badge, Change Type, Category, Importance, Confidence, AI Explanation, and Grounded Practical Impact.
- **Download PDF Report**: Generates and downloads an audit-ready PDF summary report.
- **Return to Upload Button**: Return to compare another pair of documents.

---

## 7. Running Tests

Run the full automated test suite:
```bash
cd ai-doc-compare
python -m pytest -v
```

### Test Suite Results (24 Passed):
- `test_validation_supported_formats`: Format verification for `.pdf`, `.docx`, `.txt` (PASSED)
- `test_validation_unsupported_formats`: Graceful rejection of invalid extensions (PASSED)
- `test_validation_empty_file`: 0-byte file handling (PASSED)
- `test_validation_oversized_file`: Enforces maximum file size limit (PASSED)
- `test_factory_creates_correct_adapters`: Factory Pattern instantiation (PASSED)
- `test_factory_rejects_unknown_extension`: Factory error safety (PASSED)
- `test_txt_adapter_extraction`: TXT encoding and content extraction (PASSED)
- `test_docx_adapter_extraction`: DOCX paragraphs and tables extraction (PASSED)
- `test_pdf_adapter_extraction`: PDF text stream parsing (PASSED)
- `test_pdf_corrupted_handling`: PDFStreamError exception handling (PASSED)
- `test_preprocessor_structuring`: Section and paragraph structuring (PASSED)
- `test_matcher_detects_all_change_types`: Detection of ADDED, DELETED, MODIFIED, UNCHANGED (PASSED)
- `test_strategy_pattern_execution_and_switching`: Strategy Pattern runtime swapping (PASSED)
- `test_meaningful_attendance_requirement_change`: **Mandatory 75% → 80% attendance requirement test** (PASSED)
- `test_wording_only_change`: **Mandatory wording-only test** (*"must submit"* vs *"are required to submit"*) (PASSED)
- `test_addition_and_removal_classification`: Additions and removals categorization (PASSED)
- `test_rag_chunking_and_retrieval`: Local vector index and dual-document retrieval (PASSED)
- `test_ai_fallback_when_credentials_missing`: Graceful fallback preserving full comparison (PASSED)
- `test_pdf_report_generation`: Valid `%PDF` binary generation (PASSED)
- `test_api_health`: `/api/health` diagnostic endpoint (PASSED)
- `test_api_compare_txt`: End-to-end TXT comparison via API (PASSED)
- `test_api_compare_docx`: End-to-end DOCX comparison via API (PASSED)
- `test_api_compare_pdf`: End-to-end PDF comparison via API (PASSED)
- `test_api_download_pdf_report`: PDF download endpoint (PASSED)

---

## 8. Graceful Degradation & Known Limitations

- **OCR Dependency**: Scanned PDF fallback relies on Tesseract OCR. If Tesseract is not installed on the system, the application catches the condition gracefully, notes that OCR is not configured, and continues without crashing.
- **External AI Providers**: When no external LLM API key (`OPENAI_API_KEY`, `GEMINI_API_KEY`) is configured, the system uses its embedded local semantic reasoning and vector RAG engine.

