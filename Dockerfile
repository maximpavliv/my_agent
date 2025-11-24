FROM ubuntu:22.04

# Install basic utilities
RUN apt-get update && apt-get install -y \
    bash \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a working directory
WORKDIR /workspace

# Keep container running
CMD ["tail", "-f", "/dev/null"]

