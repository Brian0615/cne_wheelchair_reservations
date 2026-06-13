# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

CNE Wheelchair Reservations is a two-service application (FastAPI API + Streamlit UI) for managing wheelchair and
scooter rentals at the Canadian National Exhibition. All persistent data lives in AWS DynamoDB; completed rental PDFs
are stored in S3.

## Commands

### Local development (without Docker)

```bash
# Create conda environment
conda env create -f conda_env.yml

# Run tests
python -m pytest tests/

# Run tests with coverage
python -m pytest --cov=api --cov=ui --cov=common --cov-report=html tests/

# Run a single test file
python -m pytest tests/path/to/test_file.py

# Run a single test class or method
python -m pytest tests/path/to/test_file.py::ClassName::test_method
```

Required environment variables for local testing (see `api.env` / `ui.env` for examples):

- `API_HOST`, `API_PORT`, `AUTH_METHOD`, `AUTH_CONFIG_PATH`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`,
  `AWS_DEFAULT_REGION`, `PDF_PASSWORD`, `S3_BUCKET`, `CNE_YEAR`
- `GEMINI_API_KEY` — Google AI Studio key used by the chatbot (`api/src/chat_service.py`); only needed when actually
  calling the chatbot. Optionally `GEMINI_MODEL` (defaults to `gemini-3.1-flash-lite`).

### Docker

```bash
# Build and run all services (loads env from api.env + ui.env)
./run.sh

# Build images
docker compose build

# Build and push to Docker Hub
docker compose push
```

The compose file uses Docker secrets sourced from environment variables. Images target both `linux/amd64` and
`linux/arm64`.

## Architecture

### Services

**API** (`api/`, port 8595) — FastAPI app. Entry point: `api/main.py`.

- Routers in `api/routers/`: `devices`, `rentals`, `reservations`, `settings`, `chat`
- All routers delegate to `api/src/dynamodb_service.py` (`DynamoDBService`) for persistence
- `api/src/s3_service.py` handles PDF upload/download
- `api/src/chat_service.py` runs the chatbot: a `pydantic-ai` agent (Google Gemini) whose tools are thin wrappers
  over `DynamoDBService`. The agent is built lazily so importing the module needs no `GEMINI_API_KEY`. App-usage help
  is sourced from `api/assets/reservations_manual.md` (regenerate this from `CNE Wheelchair Reservations Manual.docx`
  whenever the manual changes). This is the only `pydantic-ai`-coupled module, keeping a later framework swap localized.
- Router functions are decorated with `@auto_process_database_errors` (`api/src/utils.py`) to convert domain exceptions
  to HTTP 400/404 responses

**UI** (`ui/`, port 8095) — Streamlit app. Entry point: `ui/main.py`.

- Page navigation is role-gated: all users see Home/Rentals/Reservations/Inventory; admin users get
  reservation/inventory management plus the Chatbot (`ui/ui_pages/chatbot.py`); editor users get rental
  creation/management
- Pages live in `ui/ui_pages/`; reusable form field components in `ui/forms/`
- PDF forms are filled via PyMuPDF in `ui/pdf_forms/` using fillable PDFs from `ui/assets/`

**Common** (`common/`) — shared enums, Pydantic data models, logger, utils, and CNE date helpers
(`common/cne_dates.py` `CNEDates`) used by both services.

### Data layer

DynamoDB tables all share the composite key `cne_year` (hash) + `id` (range):

- `cne_devices` / `cne_devices_test`
- `cne_rentals` / `cne_rentals_test`
- `cne_reservations` / `cne_reservations_test`
- `cne_settings` / `cne_settings_test`

Set `DEV_MODE=true` to route all DynamoDB calls to the `_test` tables, keeping production data isolated.

**ID format**: `[prefix][MMDD][sequence]` — e.g., `W0820001` is the first wheelchair rental/reservation on Aug 20.
Device IDs use `[prefix][NN]` (e.g., `W01`, `S03`). Prefixes: `W` = Wheelchair, `S` = Scooter.

**CNE_YEAR** scopes all data — always passed as the DynamoDB partition key.

### Authentication

`ui/auth/` implements a `BaseAuthenticator` with two concrete backends selected by the `AUTH_METHOD` env var:

- `local` — `LocalAuthenticator` using `streamlit-authenticator` with credentials from `AUTH_CONFIG_PATH`
- `cognito` — `CognitoAuthenticator` using AWS Cognito (requires `AWS_COGNITO_*` secrets)

Role checks (`is_admin_user()`, `is_editor_user()`) are enforced in `ui/main.py` before pages are registered in the
navigation.

### Tests

Tests use `unittest.TestCase` with pytest as the runner. Three base classes in `tests/base_tests.py`:

- `BaseTestCases.BaseDynamoDBServiceTest` — wraps tests in `@mock_aws` (moto), creates/tears down DynamoDB tables per
  test, provides mock data generators
- `BaseTestCases.BaseFormFieldTest` — tests Streamlit form field components via `AppTest.from_function`
- `BaseTestCases.BaseUIPageTest` — tests full Streamlit pages via `AppTest.from_file`, patches HTTP requests with
  `MockRequests` and patches `LocalAuthenticator`

`tests/conftest.py` suppresses noisy "missing ScriptRunContext" warnings that Streamlit emits during tests.

The following folders should be checked for coverage: `api`, `ui`, `common`. The `tests` folder itself should not be
included in coverage.

The following environment variables are required for tests:

- `API_HOST`: can be set to any value since tests patch HTTP requests to the API
- `API_PORT`: can be set to any value since tests patch HTTP requests to the API
- `AUTH_CONFIG_PATH`: can be set to any value since tests patch the authenticator to bypass actual auth
- `AWS_ACCESS_KEY_ID`: can be set to any value since moto doesn't validate credentials
- `AWS_DEFAULT_REGION`: can be set to any value since moto doesn't validate credentials
- `AWS_SECRET_ACCESS_KEY`: can be set to any value since moto doesn't validate credentials
- `PDF_PASSWORD`: can be set to any value since PDF form tests don't actually generate PDFs
- `AUTH_METHOD`: should be set to `local

### CI/CD

`.github/workflows/ci-cd.yml` runs on every push/PR:

1. Snyk vulnerability scan
2. Unit tests (Python 3.13, pip install from `requirements.txt`)
3. Build and push multi-arch Docker images to Docker Hub (only on `main`, tags, or releases)
4. Deploy to ECS (only on `main`)
