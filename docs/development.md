# Development setup

## Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
cp config/example.env .env
```

The values in `config/example.env` point at DynamoDB Local on `http://localhost:8000` with dummy credentials. DynamoDB Local accepts any credentials.

## Running everything with one command

With Docker running:

```bash
scripts/run_local.sh
```

It creates `.env` if it is missing, starts DynamoDB Local in Docker (or reuses one already on port 8000), creates the tables, and runs the app on [http://127.0.0.1:5000](http://127.0.0.1:5000). Ctrl+C stops the app and the DynamoDB Local container it started. To load the sample data, run `python scripts/seed.py` in another terminal.

The sections below do the same steps by hand.

## DynamoDB Local

Start DynamoDB Local bound to `127.0.0.1` only, so it is not reachable from other machines. Data is kept in `db/` at the repository root, which is gitignored.

With Docker:

```bash
mkdir -p db
docker run --rm -p 127.0.0.1:8000:8000 -v "$PWD/db:/home/dynamodblocal/db" \
  amazon/dynamodb-local -jar DynamoDBLocal.jar -sharedDb -dbPath ./db
```

Or with the [downloadable JAR](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.DownloadingAndRunning.html) (requires Java):

```bash
java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar \
  -sharedDb -dbPath ./db -port 8000
```

`-sharedDb` makes every client see the same tables regardless of the credentials and region it uses.

## Tables and sample data

```bash
python scripts/create_tables.py      # create any missing tables
python scripts/seed.py               # load specs/sample-data.json
python scripts/seed.py --reset       # delete and recreate the tables, then load
python scripts/seed.py --file other.json
```

`--reset` only runs when `DYNAMODB_ENDPOINT_URL` points at `localhost`, `127.0.0.1`, or `::1`.

## Running the application

```bash
python -m volunteer_signup.app
```

Open [http://127.0.0.1:5000/health](http://127.0.0.1:5000/health). It returns `{"status": "ok"}` when DynamoDB Local is reachable and the tables exist, and `503` with `{"status": "unavailable"}` otherwise.

On macOS, AirPlay Receiver also listens on port 5000, so `http://localhost:5000` can return an empty `403` from AirPlay instead of reaching Flask. Use `127.0.0.1`, or turn off AirPlay Receiver in System Settings.

## Tests

```bash
pytest tests
ruff check src tests scripts
```

Playwright UI tests live in `tests_ui/` and need DynamoDB Local plus the app:

```bash
pytest tests_ui
```

Tests use moto instead of DynamoDB Local, so they need no running database. `tests/conftest.py` provides two fixtures:

- `db`: a `Database` with empty tables.
- `seeded_db`: the same, loaded with `specs/sample-data.json`.

## Code layout

```text
src/volunteer_signup/
  app/        Flask app factory (factory.py) and route blueprints (routes/)
  service/    application rules between the routes and the database
  db/         DynamoDB access: tables.py, reads.py, writes.py, seed.py
  config/     settings loaded from .env
  templates/  Jinja templates
  static/     CSS, JavaScript, and images
```

`volunteer_signup.db` exposes the `Database` class and its exceptions (`NotFoundError`, `ShiftTakenError`, `EventIdTakenError`, `DatabaseError`). Only `db/` imports boto3.
