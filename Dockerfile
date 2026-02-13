FROM python:3.11-slim

# Python env
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Instala dependências do sistema e Java
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    git \
    default-jdk \
    python3-venv \
    libldap2-dev \
    libsasl2-dev \
    && rm -rf /var/lib/apt/lists/*


ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"

RUN java -version

# Copia arquivos antes do pip install
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Cria virtualenv e instala dependências
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --upgrade pip && \
    pip install wbjdbc && \
    pip install -e ".[dev,ide,database,auth]"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/health', timeout=5)" || exit 1

CMD ["uvicorn", "fglinterpreter.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
