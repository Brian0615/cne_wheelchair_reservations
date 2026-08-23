# Observability

## Logging

Both services log structured, single-line JSON via `common.logger.initialize_logger()` (see
`common/logger.py`). Every log line includes `timestamp`, `level`, `logger`, `message`,
`request_id`, and `username`, plus any ad-hoc fields passed via `extra={...}` (for example
`duration_ms`, `status_code`, `rental_id`, `reservation_id`, `device_id`).

- `LOG_LEVEL` (env var, e.g. `DEBUG`/`INFO`/`WARNING`/`ERROR`) controls verbosity; it defaults to
  `DEBUG` if unset.
- `request_id`: a UUID generated per API request (or per UI script rerun) and propagated between
  the UI and API via the `X-Request-ID` header, so every log line touched by one user action can be
  found with a single query.
- `username`: the logged-in user, attached to every UI-side log line after `initialize_page`
  authenticates them.

## CloudWatch alarm readiness

This repo does not configure CloudWatch itself — logs currently go to each container's
stdout/stderr, captured locally by Docker's default log driver. Before any of the signals below can
back a CloudWatch alarm, **the ECS task definition (outside this repo) needs to configure the
`awslogs` log driver with a log group and retention policy** so container output actually reaches
CloudWatch Logs. That wiring is a separate follow-up ticket.

Once logs reach CloudWatch, the following are ready to back metric filters/alarms without any
further change to the log content:

| Signal | Metric filter pattern (example) | Why it matters |
|---|---|---|
| API error rate | `{ $.level = "ERROR" }` on the API log group | Unhandled exceptions (`api/main.py`'s global exception handler) |
| API request latency (p95/p99) | `$.duration_ms` on `"Request completed"` lines | Per-request timing from `RequestContextMiddleware` |
| Chatbot rate-limit fallback frequency | `{ $.message = "Chatbot model * hit its rate limit*" }` | A spike means the Gemini model fallback chain is close to being exhausted |
| DynamoDB `ConditionalCheckFailed` frequency | `{ $.message = "One or more devices not found in the inventory*" }` | A spike could indicate a UI bug causing repeated invalid mutation attempts |
| UI-side API connection failures | `{ $.level = "ERROR" && $.logger = "ui.src.data_service" }` | Signals the API is unreachable from the UI's perspective |
| S3 errors | `{ $.level = "ERROR" && $.logger = "api.src.s3_service" }` | Non-`NoSuchKey` S3 failures (upload/download) |

`request_id` and `username` aren't alarm signals themselves, but they're what an on-call engineer
uses to pivot from an alarm-linked log line to every other log line for that request/user across
both services.
