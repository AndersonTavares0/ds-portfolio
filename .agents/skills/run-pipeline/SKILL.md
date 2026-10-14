---
name: run-pipeline
description: Start the ds-portfolio data stack, run the pipeline end to end, and diagnose the failure modes that actually occur in this repository — Docker port collision with a native PostgreSQL, TLS interception during download, and empty-string casts in the raw layer. Use when the pipeline fails, when asked to run or verify it, or when setting the project up on a new machine.
---

# Run the pipeline

## Normal path

```bash
uv run python tasks.py doctor       # environment sanity: docker, python, data
uv run python tasks.py db-up        # start PostgreSQL, wait for healthy
uv run python tasks.py data         # download + validate (~126 MB, once)
uv run python tasks.py load         # CSVs -> the `raw` schema
uv run python tasks.py dbt-build    # models AND tests
uv run python tasks.py test         # Python tests
```

Or `uv run python tasks.py pipeline` for the last four in order.

Never call `docker`, `dbt` or `pytest` directly. `tasks.py` is what loads `.env`
and sets `PYTHONPATH`, and dbt does not read `.env` on its own.

## What success looks like

- `load` prints all nine tables with matching row counts, `ok` on each
- `dbt-build` ends with `PASS=38 ERROR=0` (9 views + 29 tests)
- `pytest` ends with `18 passed`

Row counts on a correct load: customers 99,441 · geolocation 1,000,163 ·
order_items 112,650 · order_payments 103,886 · order_reviews 99,224 ·
orders 99,441 · products 32,951 · sellers 3,095 · categories 71.

## Failure modes that actually happen here

### 1. `password authentication failed for user "portfolio"`

**Almost never a wrong password.** A PostgreSQL installed natively on the machine
binds `0.0.0.0:5432` and silently shadows the container's port mapping, so the
connection reaches the wrong server.

Confirm it:

```bash
docker port ds-portfolio-db          # expect 5432/tcp -> 0.0.0.0:5433
docker exec -e PGPASSWORD=portfolio ds-portfolio-db psql -h 127.0.0.1 -U portfolio -d olist -tAc "select current_user"
```

If the `docker exec` works but the host connection does not, it is the collision.
The fix is already in place: the host port defaults to **5433**. If you changed
`POSTGRES_PORT`, make sure `config.py` and `profiles.yml` agree with it.

Do **not** "fix" this by stopping the user's native PostgreSQL — it may be a
system service they rely on.

### 2. `SSLCertVerificationError: self-signed certificate in certificate chain`

Something between the machine and the internet (corporate proxy, or antivirus
such as Kaspersky/ESET/Zscaler) is decrypting HTTPS with its own root
certificate. `requests` verifies against the `certifi` bundle, which does not
know that root — which is also why `curl` succeeds where Python fails, since
`curl` uses the OS store.

The downloader already tries the OS store via `truststore`. If it still fails:

- point Python at the root explicitly: `REQUESTS_CA_BUNDLE=/path/to/ca-bundle.crt`
- or install the intercepting root into the system store

Note: `truststore` renamed `inject_ssl_context` to `inject_into_ssl` in 0.10.
`retail.io` accepts both; do not "simplify" it back to one name.

### 3. `invalid input syntax for type timestamp: ""`

The loader writes every raw column as TEXT and keeps empty cells as empty
strings, so the raw table is a faithful copy of the CSV. A bare
`cast(col as timestamp)` therefore fails on real data.

Fix it with the macros, never with a bare cast:

```sql
{{ safe_timestamp('order_approved_at') }} as approved_at
{{ safe_integer('product_weight_g') }}    as weight_grams
{{ safe_numeric('payment_value') }}       as payment_value
```

### 4. Download fails partway

Re-run `uv run python tasks.py data`. Files that already match their expected
byte size are skipped, so a resumed download only fetches what is missing. Use
`--force` only when you deliberately want to re-download everything.

## Tearing down

```bash
uv run python tasks.py db-down      # stop, keep the data volume
uv run python tasks.py db-reset     # stop and DELETE the volume
```

`db-reset` destroys the loaded data. It is free only when nothing is loaded yet.
