# ==========================
# STAGE 1: Base image
# ==========================

# Use official lightweight Python image (version 3.12-slim)
FROM python:3.12-slim

# ==========================
# Environment setup
# ==========================

# Prevent Python from writing .pyc files and buffering output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory inside the container
WORKDIR /app

# Copy dependency list first (to leverage Docker caching)
COPY requirements.txt .

# Install dependencies
# --no-cache-dir → prevents storing pip cache, keeping the image small
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the source code into the image
COPY . .

# ==========================
# Container runtime configuration
# ==========================

# Expose the port FastAPI will run on (matches app_port in .env)
EXPOSE 8000

# Default command to start the FastAPI app using Uvicorn
# --host 0.0.0.0 makes it accessible outside the container
# --reload is disabled in production but helpful during dev
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
