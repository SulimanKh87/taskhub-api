# === Base Image ===
FROM python:3.12-slim

# === Set working directory ===
WORKDIR /code

# === Create a non-root user for security ===
RUN useradd -m appuser

# === Copy requirements and install dependencies ===
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# === Copy app code ===
COPY app ./app

# === Use non-root user ===
USER appuser

# === Expose API port ===
EXPOSE 8080

# === Start FastAPI server ===
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
