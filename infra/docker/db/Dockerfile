# Local PostgreSQL for AdvisorFlow AI (Compose service `db`).
# Extends official image so you can layer init scripts later (COPY ... /docker-entrypoint-initdb.d/).

FROM postgres:16-alpine

ENV POSTGRES_DB=advisorflow
ENV POSTGRES_USER=advisorflow
ENV POSTGRES_PASSWORD=advisorflow

EXPOSE 5432
