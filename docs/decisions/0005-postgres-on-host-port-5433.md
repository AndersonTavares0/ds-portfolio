# 0005 — PostgreSQL runs on host port 5433

**Status:** Accepted
**Date:** 2026-10-14

## Situation

The first `tasks.py load` failed with:

```
psycopg.OperationalError: password authentication failed for user "portfolio"
```

The credentials were correct. The container had the right environment
(`POSTGRES_USER=portfolio`, `POSTGRES_PASSWORD=portfolio`, `POSTGRES_DB=olist`),
the application defaults matched, and a `psql` run *inside* the container
authenticated successfully. The error message pointed at the password, and the
password was not the problem — which is what made this expensive to find.

`Get-NetTCPConnection -LocalPort 5432` showed the cause: a **native PostgreSQL
already listening on `0.0.0.0:5432` and `[::]:5432`** on the host. Docker's port
mapping published the container on the same port, and the host's own PostgreSQL
answered first. The application connected to the wrong database and was told its
password was wrong.

## Decision

The container keeps 5432 **inside** Docker and publishes **5433** on the host:

```yaml
ports:
  - "${POSTGRES_PORT:-5433}:5432"
```

`POSTGRES_PORT` defaults to 5433 in `.env.example`, `src/retail/config.py` and
`dbt_project/profiles.yml`.

## Consequences

- **Costs:** the port is not the default, so it has to be stated in every place a
  connection is built — which is why it is documented here, in the project README,
  in `AGENTS.md` and in the run-pipeline skill. A number that must be repeated
  four times should be repeated four times.
- **Buys:** a fresh clone connects on the first try, on any machine. This was not
  only a Windows problem: Fedora ships PostgreSQL and commonly has it listening on
  5432, so the collision would have appeared on the development machine too — and
  would have looked, again, like a wrong password.
- **Deliberately not done:** stopping or reconfiguring the host's PostgreSQL. That
  database belongs to the user and this project has no business touching it. A
  project that requires you to disable something else on your machine to run is a
  project with a port problem, not a project with a setup step.
- **CI is unaffected:** the GitHub Actions service container is its own isolated
  network namespace with nothing else on 5432, so the workflow there keeps the
  default port on purpose.
