FROM python:3.11

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# ✅ expose internal container port (not critical but good)
EXPOSE 8000

# ✅ Production command (Railway compatible)
CMD ["sh", "-c", "gunicorn -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:$PORT --workers 2 --log-level info"]