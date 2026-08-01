# Reproducible runtime for the data-refresh pipeline.
# Bundles Python + a JRE, because convert2txt.py converts the doc/docx/pdf
# records with tika-app-1.20.jar (Java). Baking both in means the scheduled
# incremental run behaves identically wherever it runs (GitHub Actions, a VPS,
# a cloud job) with no manual Java setup.
FROM python:3.11-slim

# default-jre-headless is the Java runtime that tika-app-1.20.jar needs
RUN apt-get update \
    && apt-get install -y --no-install-recommends default-jre-headless \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# install python deps first so the layer is cached across code changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# the scripts use paths relative to src/ and invoke tika by a relative jar name,
# so the entry point must run from there
WORKDIR /app/src

# default command: the incremental refresh. The scheduler passes the watermark,
# e.g.  docker run <image> --since 2026-07-20
ENTRYPOINT ["python", "run_incremental.py"]
