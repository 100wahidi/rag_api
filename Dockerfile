FROM python:3.11-slim

# Install system dependencies & minimal LaTeX tools (if compiling PDFs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    texlive-latex-base \
    texlive-fonts-recommended \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv for fast, reliable package installations
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency specifications
COPY pyproject.toml uv.lock ./

# Install locked dependencies into the system environment
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy application source code
COPY . .

# Run uvicorn dynamically binding to Railway's $PORT (default to 8000 locally)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
