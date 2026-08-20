# PostgreSQL for the Nuets Food AI Service.
#
# Build + run with docker compose (recommended):
#   docker compose up -d
#
# Or standalone:
#   docker build -t nuets-postgres ./docker
#   docker run -d --name nuets-postgres -p 5432:5432 \
#     -e POSTGRES_USER=macbook-pro -e POSTGRES_PASSWORD=Mini@pass001 \
#     -e POSTGRES_DB=postgres -v nuets_pgdata:/var/lib/postgresql/data nuets-postgres
FROM postgres:16-alpine

# Matches the credentials the service connects with. Override at run time with
# -e POSTGRES_USER / -e POSTGRES_PASSWORD.
ENV POSTGRES_USER=macbook-pro \
    POSTGRES_PASSWORD=Mini@pass001 \
    POSTGRES_DB=postgres

# Scripts in this directory are executed once, in name order, the first time the
# data volume is initialised.
COPY init/ /docker-entrypoint-initdb.d/

EXPOSE 5432
