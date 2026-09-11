FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for compiling wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and set up caching behavior
RUN pip install --no-cache-dir --upgrade pip

# Copy only requirements first to leverage caching
COPY requirements.txt .

# Install heavy foundational libraries individually first (prevents parallel RAM spikes)
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir chromadb
RUN pip install --no-cache-dir langchain langchain-google-genai

# Install the rest of whatever is left in your requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app code
COPY . .

CMD ["./scripts/start_production.sh"]