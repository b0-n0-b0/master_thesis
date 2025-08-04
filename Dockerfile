# Use specific Python 3.8.20 base image due to Manticore needs
FROM python:3.8.20-slim

# Install system dependencies for building repos
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    cmake \
    m4 \
    unzip \
    bubblewrap \
    libgmp-dev \
    sudo \
    ca-certificates \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Install opam
RUN curl -fsSL https://raw.githubusercontent.com/ocaml/opam/master/shell/install.sh | sh

# NOTE: non-interactive, not sure why but on VPSs the previous one does not work, let's skip to this one
# Manually install a specific OPAM version non-interactively
# ENV OPAM_VERSION=2.3.0
# RUN curl -fsSL https://github.com/ocaml/opam/releases/download/${OPAM_VERSION}/opam-${OPAM_VERSION}-x86_64-linux \
#     -o /usr/local/bin/opam && \
#     chmod +x /usr/local/bin/opam

# Initialize opam (non-interactive, no sandbox)
ENV OPAMYES=true
RUN opam init --disable-sandboxing -a -y && \
    opam update && \
    eval $(opam env)
RUN opam install core_unix.v0.16.0
RUN opam install wasm.2.0.1

# Set working directory

# Clone and build wassail
RUN git clone https://github.com/b0-n0-b0/wassail-master_thesis.git /wassail
WORKDIR /wassail 
RUN opam install . 
RUN eval $(opam env)

WORKDIR /app

COPY requirements.txt .
# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy Python app into the image
COPY . /app


# Entry point with argument support
# ENTRYPOINT ["python", "main.py"]
# CMD ["python", "main.py"]
ENTRYPOINT ["opam", "exec", "--", "python", "main.py"]
