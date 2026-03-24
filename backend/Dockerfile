FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN groupadd -r owbc && useradd -r -g owbc owbc

# Install runtime dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir python-magic

COPY app ./app

# Ensure the non-root user owns the app directory and any necessary subdirectories
RUN mkdir -p /app/uploads && chown -R owbc:owbc /app

USER owbc

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
