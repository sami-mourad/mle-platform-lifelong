FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --upgrade pip && pip install .

COPY configs ./configs
COPY infra/docker ./infra/docker
COPY scripts ./scripts

RUN mkdir -p /app/.data /app/.artifacts /app/.dagster

EXPOSE 8000 3000 4000 5000
CMD ["python", "-m", "mle_platform.projects.dummy_imbalance.service"]
