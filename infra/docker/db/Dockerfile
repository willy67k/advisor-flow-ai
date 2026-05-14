# Local PostgreSQL for AdvisorFlow AI (Compose service `db`).
# Extends official image so you can layer init scripts later (COPY ... /docker-entrypoint-initdb.d/).

# Postgres 16 + pgvector (required for Phase 5 RAG embeddings).
FROM pgvector/pgvector:pg16

ENV POSTGRES_DB=advisorflow
ENV POSTGRES_USER=advisorflow
ENV POSTGRES_PASSWORD=advisorflow

EXPOSE 5432
