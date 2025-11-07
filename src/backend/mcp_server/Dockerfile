# Multi-stage build for smaller final image
FROM python:3.12-slim as builder

# Install build dependencies only in builder stage
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy requirements first for better layer caching
COPY ./mcp_server/requirements.txt /build/requirements.txt

# Install Python dependencies to a local directory
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage - minimal runtime image
FROM python:3.12-slim

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /src

# Copy Python packages from builder stage
COPY --from=builder /root/.local /root/.local

# Copy the mcp directory (including services and synthetic datasets)
COPY ./mcp_server /src/mcp_server

# Make sure local bin is in PATH
ENV PATH=/root/.local/bin:$PATH

EXPOSE 12321

CMD ["python3", "/src/mcp_server/app.py"]