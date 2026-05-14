FROM node:22-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    git \
    procps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Set TERM so terminal-based QR codes render properly
ENV TERM=xterm-256color

# Create a non-root user for safety
RUN useradd -m -s /bin/bash claude && chown -R claude:claude /app
USER claude

# Entrypoint — we'll override with commands as needed
ENTRYPOINT ["/bin/bash"]
