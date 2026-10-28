# Legacy App to Microservices Migration

> This README was generated with [Claude](https://claude.ai) by Anthropic under my command and properly checked by me.

![Python](https://img.shields.io/badge/Python-FastAPI-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-CI-2088FF?logo=githubactions&logoColor=white)

A small, realistic example of moving a monolithic app to microservices: a Flask app with one SQLite
file is split into two independent REST services, each with its own PostgreSQL database, its own
SQL migrations, its own tests and its own CI pipeline. A migration script moves the existing data
across through the new APIs.

## The problem

`legacy/app.py` handles accounts **and** trades in one process with one SQLite file.

- A change to trades means redeploying and retesting accounts too.
- SQLite is a local file, so the app can't run on more than one server.
- There is no input validation: a trade with quantity `-5` or a made-up ISIN is accepted.
- The schema is created in code, with no history of how it changed.

## The solution

|                       | Legacy                 | After migration                                                         |
| --------------------- | ---------------------- | ----------------------------------------------------------------------- |
| Services              | 1 Flask app            | `accounts` and `trades` (FastAPI)                                       |
| Database              | 1 SQLite file          | PostgreSQL, one database per service                                    |
| Schema changes        | `CREATE TABLE` in code | versioned `.sql` migrations, applied once on startup                    |
| Validation            | none                   | Pydantic models: ISIN format, `BUY`/`SELL`, positive quantity and price |
| Talking to each other | shared tables          | HTTP: trades asks accounts if an account exists                         |
| Tests and CI          | none                   | pytest per service, GitHub Actions builds and Trivy-scans each image    |
| API docs              | none                   | OpenAPI, generated automatically at `/docs`                             |

```mermaid
flowchart LR
    subgraph before[Before]
        legacy[Flask monolith] --> sqlite[(SQLite)]
    end

    subgraph after[After]
        acc[accounts service] --> accdb[(Postgres: accounts)]
        tr[trades service] --> trdb[(Postgres: trades)]
        tr -->|GET /accounts/id| acc
    end

    sqlite -->|scripts/migrate_data.py<br/>via the new APIs| acc
    sqlite --> tr
```

## The result

- Each service is tested, built and deployed on its own, so a change to trades never touches accounts.
- Bad data is rejected at the API with a clear error (`422`), and if the accounts service is down,
  trades answers `503` instead of saving a trade for an account nobody checked.
- Every schema change is a reviewed `.sql` file, and the `schema_migrations` table shows what ran when.
- The data migration is safe to run twice: accounts keep their old id in `legacy_id`, so nothing is duplicated.

## Project layout

```
legacy/                  the old monolith (Flask + SQLite) and a seed script
services/accounts/       FastAPI service, migrations/, tests/, Dockerfile
services/trades/         FastAPI service, migrations/, tests/, Dockerfile
scripts/migrate_data.py  copies legacy data into the new services through their APIs
db/init.sql              creates one database per service in the Postgres container
docker-compose.yml       runs Postgres and both services together
.github/workflows/ci.yml test, build and scan each service separately
```

## Run it

You need Docker (with Compose) and Python 3.12.

```bash
# 1. Start Postgres and both services
docker compose up --build -d
curl localhost:8001/health      # {"status":"ok","service":"accounts"}
curl localhost:8002/health      # {"status":"ok","service":"trades"}

# 2. Create the legacy data
python -m venv .venv && source .venv/bin/activate
pip install flask==3.0.3 httpx==0.28.1
cd legacy && python seed.py && cd ..

# 3. Migrate it into the new services (run it twice: the second run changes nothing)
python scripts/migrate_data.py legacy/legacy.db

# 4. Look at the result
curl localhost:8001/accounts
curl "localhost:8002/trades?account_id=1"
```

Open <http://localhost:8001/docs> and <http://localhost:8002/docs> to try the APIs in the browser.

Try the error cases too:

```bash
# Unknown account -> 422
curl -X POST localhost:8002/trades -H 'Content-Type: application/json' \
  -d '{"account_id": 99, "isin": "DE0005810055", "side": "BUY", "quantity": 1, "price": "10"}'

# Accounts service down -> 503
docker compose stop accounts
curl -X POST localhost:8002/trades -H 'Content-Type: application/json' \
  -d '{"account_id": 1, "isin": "DE0005810055", "side": "BUY", "quantity": 1, "price": "10"}'
docker compose start accounts
```

## Run the tests

The tests use a real Postgres database (the one from Compose works):

```bash
cd services/accounts
pip install -r requirements.txt
DATABASE_URL=postgresql://app:app@localhost:5432/accounts pytest -v
```

Same for `services/trades` with `.../trades`. The trades tests replace the accounts service with a
fake, so they don't need it running.

## Stop and clean up

```bash
docker compose down -v   # -v also deletes the database volume
```

## Ideas to extend it

- Add a third migration, for example a `status` column on trades, and watch it apply on restart.
- Push the images to a registry from CI and deploy them to the minikube cluster from
  [iac-lab](https://github.com/Dinesh16680-M/iac-lab).
- Add a `/metrics` endpoint with `prometheus-fastapi-instrumentator`.
