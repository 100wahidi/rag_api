# ==============================================================================
# STAGE 1: Dependency Resolver & Builder
# ==============================================================================
FROM python:3.11-slim-bookworm AS builder

# Grab the hardened, pre-compiled uv binary from Astral's official distribution
COPY --from=ghcr.io/astral-sh/uv:0.6.2 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 1. Cache Boundary: Copy ONLY manifest files to leverage Docker layer caching
COPY pyproject.toml uv.lock ./

# 2. Synchronize dependencies strictly from lockfile into an isolated virtual environment
#    --frozen: Abort if uv.lock does not match pyproject.toml
#    --no-dev: Strip test/lint tooling from production artifacts
#    --no-install-project: Install dependencies only, before copying application source
RUN uv sync --frozen --no-dev --no-install-project

# 3. Copy application codebase and install the project itself
COPY . .
RUN uv sync --frozen --no-dev

# ==============================================================================
# STAGE 2: Minimal Production Runtime
# ==============================================================================
FROM python:3.11-slim-bookworm AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

# Install solely essential runtime binaries (minimal TeX + supervisor)
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-fonts-recommended \
    lmodern \
    tini \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Strict Assertion: Enforce binary contract at build-time
RUN which pdflatex || exit 1

# Security: Dedicated unprivileged execution identity
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -m -s /bin/bash appuser

WORKDIR /app

# Copy the isolated virtualenv and application artifacts from the builder
COPY --from=builder --chown=appuser:appgroup /app /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8000') + '/health', timeout=3)"

# Supervisor entrypoint to handle signal propagation and reap zombie subprocesses
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]