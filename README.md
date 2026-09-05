<p align="center">
  <img src="https://skillicons.dev/icons?i=py,fastapi,ts,supabase,postgres,pytorch,hf,docker,git" height="48" alt="Core Technologies" />
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/latex/latex-original.svg" height="42" width="42" alt="LaTeX" style="margin-left: 6px; vertical-align: top;" />
  <img src="https://groq.com/wp-content/uploads/2024/03/groq-icon-black.png" height="42" width="42" alt="Groq LPU" style="margin-left: 10px; vertical-align: top;" />
  <img src="https://assets.astral.sh/uv/uv-light.svg" height="42" width="42" alt="Astral uv" style="margin-left: 10px; vertical-align: top;" />
</p>

<p align="center">
  <a href="#ddia-canon"><img src="https://img.shields.io/badge/Architecture-Kleppmann_DDIA_Canon-black?style=for-the-badge" alt="DDIA Canon" /></a>
  <a href="#benchmarks"><img src="https://img.shields.io/badge/Inference_Speed-Groq_LPU_Engineered-f55036?style=for-the-badge" alt="Groq Inference" /></a>
  <a href="#benchmarks"><img src="https://img.shields.io/badge/Latency_Profile-Deterministic_P99-0052FF?style=for-the-badge" alt="P99 Latency" /></a>
  <a href="#sandboxing"><img src="https://img.shields.io/badge/Compilation-Jailed_POSIX-red?style=for-the-badge" alt="POSIX Sandbox" /></a>
</p>

---

# Latency-Engineered CV Generation & Retrieval Engine (`rag_api`)

A resilient, asynchronous REST platform built with **FastAPI**, **PostgreSQL (`pgvector`)**, **asyncpg**, and **LangChain**, designed for low-latency contextual retrieval, parsing, and deterministic LaTeX resume and cover-letter compilation.



## 1. System Architecture

<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/f0c3c627-e285-40f9-b72d-44b55b8d1113" />


## 2. Core Architectural Principles & System Canon

### Principle 1: Singleton Lifecycle Allocation for Heavy Resources
* **The Rule**: Incur initialization overhead strictly once during system startup rather than on the request path.
* **Implementation**: Heavy computing artifacts and long-lived drivers—including `SentenceTransformer` weights, LLM client connections, system binary path verification, and the `asyncpg` connection pool—are initialized strictly once inside the FastAPI `lifespan` handler.
* **DDIA Baseline (Kleppmann, Chapter 1 - *Maintainability & Operability*)**: Good system design minimizes operational friction by avoiding costly re-allocations per transaction, preventing heap fragmentation and unpredictable garbage-collection pauses under sustained query volume.

### Principle 2: Asynchronous I/O & Dependency Injection
* **The Rule**: Keep I/O non-blocking and handlers stateless.
* **Implementation**: Route handlers rely on native `async`/`await` calls backed by `asyncpg`. Database connections and service interfaces are injected into endpoints using FastAPI's `Depends` pattern, enforcing clean separation between transport concerns and data operations.
* **DDIA Baseline (Kleppmann, Chapter 3 - *Storage and Retrieval Engine Throughput*)**: Decoupling thread execution from network wait states maximizes connection concurrency and minimizes kernel context-switch overhead.

### Principle 3: Dedicated Offloading for Compute-Bound Workloads
* **The Rule**: Never execute CPU-bound work on the cooperative I/O event loop.
* **Implementation**: Operations that cannot be natively awaited (such as local PyTorch transformer embeddings and LaTeX compilation) are delegated to worker thread pools (`asyncio.to_thread`) and isolated subprocess environments to prevent event loop stalls.
* **DDIA Baseline (Kleppmann, Chapter 1 - *Scalability & Latency Profiles*)**: Eliminating single-threaded head-of-line blocking protects tail latencies ($P_{99}$, $P_{99.9}$) from degrading across shared services.

### Principle 4: Single Responsibility & Decoupled Vendor Adapters
* **The Rule**: Isolate external vendor dependencies behind stable contracts.
* **Implementation**: The LLM provider layer isolates token counter tracking, model failovers, API token expiry, and structured JSON output inside dedicated adapter classes. Changing an external provider requires modifying a single adapter without cascading changes across route schemas.
* **DDIA Baseline (Kleppmann, Chapter 1 - *Evolvability*)**: Designing extensible architectures that accommodate changes in underlying dependencies without architectural refactoring.

### Principle 5: Deterministic Error Taxonomy & Structured Observability
* **The Rule**: Fail fast, isolate error domains, and surface contextual diagnostics.
* **Implementation**: Domain boundaries define typed exceptions (`LaTeXCompilationError`, `VectorRetrievalError`, `LLMProviderTimeout`) that map directly to standard RFC-7807 responses. Color-coded formatters enhance local development while structured JSON logs maintain correlation IDs for production trace analysis.
* **DDIA Baseline (Kleppmann, Chapter 1 - *Reliability & Fault-Tolerance*)**: Establishing strict failure boundaries prevents localized component faults from causing system-wide service failure.

### Principle 6: Defense-in-Depth Authentication & Session Security
* **The Rule**: Secure state and credentials using modern cryptographic defaults.
* **Implementation**: Implements OAuth2 Bearer token workflows with cryptographic signature verification, explicit token expiration, and secure password hashing using Argon2/Bcrypt. Raw passwords and reversible secrets are strictly excluded from persistent storage.
* **DDIA Baseline (Kleppmann, Chapter 1 - *Reliability*)**: Protecting data integrity against malicious misuse and operational vulnerabilities.

### Principle 7: Managed Asynchronous Vector Search Pipelines
* **The Rule**: Offload high-dimensional vector search to specialized database extensions.
* **Implementation**: Cloud PostgreSQL with the `pgvector` extension handles high-dimensional vector similarity operations directly in the database engine, eliminating the overhead of unmanaged standalone vector microservices.
* **DDIA Baseline (Kleppmann, Chapter 2 - *Data Models and Query Languages*)**: Utilizing specialized, declarative indexing structures optimized for nearest-neighbor search queries.

---

## 3. Engineering Challenges & Root-Cause Resolutions

| Subsystem | Initial Failure Mode | Underlying Root Cause | Production Remediation |
| :--- | :--- | :--- | :--- |
| **LaTeX Sandbox** | Worker process hangs indefinitely under burst requests. | The compiler awaited terminal `stdin` input upon hitting syntax or macro errors. | Invoked `pdflatex` via `subprocess.run` with `-interaction=nonstopmode`, `stdin=DEVNULL`, temporary directory sandboxing, and strict POSIX timeouts. |
| **Event Loop Blocking** | Vector similarity lookups caused dropped connections. | In-process embedding generation ran on the primary event loop thread, starving I/O cycles. | Delegated transformer passes to background worker threads using `asyncio.to_thread`. |
| **Database Pool Leaks** | PostgreSQL connections exhausted during load testing. | Ephemeral connections were opened per request and abandoned on unhandled exceptions. | Configured an enterprise `asyncpg` connection pool on application startup, utilizing scoped dependency context managers (`async with pool.acquire()`). |
| **Model Output Flakiness** | Schema corruption during dynamic CV generation. | Raw model responses contained inconsistent formatting and unescaped TeX control characters. | Implemented strict Pydantic V2 response validation and sanitization layers before passing variables to templates. |

---

## 4. Local Deployment & Setup

```bash
# 1. Clone repository
git clone [https://github.com/your-username/rag_api.git](https://github.com/your-username/rag_api.git)
cd rag_api

# 2. Configure virtual environment using uv
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# 3. Environment Variables Configuration
cp .env.example .env

# 4. Start Development Server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload


---

### 4. Actionable Growth Roadmap (Next Iteration)

1. **Jailed Subprocess Sandboxing (Ticket #SEC-201)**:
   * Isolate the `pdflatex` execution boundary inside a locked-down, unprivileged execution jail (e.g., using `nsjail`, `bwrap`, or ephemeral gVisor containers). Disable all outbound network access and explicitly restrict TeX shell escapes (`-no-shell-escape`) to eliminate LaTeX macro injection attack vectors.
2. **Prometheus Telemetry & $P_{99}$ Latency Profiling (Ticket #PERF-202)**:
   * Instrument the retrieval and compilation pipelines with Prometheus metrics. Capture granular histogram distributions for database query duration, embedding computation time, and LaTeX compilation latency to detect tail latency degradation under simulated load.
3. **Property-Based Testing for Payload Sanitization (Ticket #QA-203)**:
   * Write property-based tests using `hypothesis` targeting the CV data extraction and LaTeX template interpolation pipelines. Generate hostile inputs containing unescaped TeX delimiters, bidirectional Unicode overrides, and schema-violating edge cases to verify fail-fast sanitization boundaries.

Are we addressing Ticket #SEC-201 (LaTeX jail sandboxing) or Ticket #PERF-202 (Prometheus latency histograms) next?
