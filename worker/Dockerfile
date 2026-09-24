# Docling worker — Google Cloud Run Job (Phase 3, ingestion distante).
#
# Base image pinned by explicit tag (a sha256 digest cannot be honestly
# fabricated here without having built the image — capture and pin the
# resolved digest in CI after the first verified build, before using this
# Dockerfile for a production deployment).
FROM python:3.12.10-slim-bookworm@sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db

WORKDIR /worker

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libxcb1 \
        libx11-6 \
        libxext6 \
        libxrender1 \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*


# CPU-only distribution: torch is installed from the CPU wheel index to
# avoid pulling CUDA dependencies (no GPU on this Cloud Run Job).
COPY worker/requirements.txt .
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
        "torch==2.14.0+cpu" \
        "torchvision==0.29.0+cpu" \
    && pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml .
COPY src ./src
RUN pip install --no-cache-dir --no-deps -e .

# Aucun corpus n'est copié dans l'image : les documents sont téléchargés
# depuis R2 à l'exécution, traités en mémoire (voir ingestion/pipeline.py
# ::ingest), jamais persistés sur le disque du worker.
ENTRYPOINT ["python", "-m", "rag_enterprise_lab.worker.docling_worker"]
