# Observability

## Logging

Both services log a single human-readable line per event via `common.logger.initialize_logger()`
(see `common/logger.py`), formatted as:

```
2026-08-23 10:15:02 INFO api.src.dynamodb_service [-]: Inserted new rental rental_id=W0820001
```

Each line includes a timestamp, level, logger name, and the current `username` in brackets (`-` when
unknown, e.g. on the API side or before login), followed by the message and any ad-hoc fields passed
via `extra={...}` appended as `key=value` pairs (for example `duration_ms`, `status_code`,
`rental_id`, `reservation_id`, `device_id`).

- `LOG_LEVEL` (env var, e.g. `DEBUG`/`INFO`/`WARNING`/`ERROR`) controls verbosity; it defaults to
  `DEBUG` if unset.
- `username`: the logged-in user, attached to every UI-side log line after `initialize_page`
  authenticates them.

## CloudWatch alarm readiness

This repo does not configure CloudWatch itself — logs currently go to each container's
stdout/stderr, captured locally by Docker's default log driver. Before any of the signals below can
back a CloudWatch alarm, **the ECS task definition (outside this repo) needs to configure the
`awslogs` log driver with a log group and retention policy** so container output actually reaches
CloudWatch Logs. That wiring is a separate follow-up ticket.

Once logs reach CloudWatch, the following are ready to back metric filters/alarms using plain-text
filter patterns without any further change to the log content:

| Signal | Metric filter pattern (example) | Why it matters |
|---|---|---|
| API error rate | `"ERROR"` on the API log group | Unhandled exceptions (`api/main.py`'s global exception handler) |
| API request latency (p95/p99) | `"Request completed" "duration_ms="` | Per-request timing from `AccessLogMiddleware` |
| Chatbot rate-limit fallback frequency | `"Chatbot model" "hit its rate limit"` | A spike means the Gemini model fallback chain is close to being exhausted |
| DynamoDB `ConditionalCheckFailed` frequency | `"One or more devices not found in the inventory"` | A spike could indicate a UI bug causing repeated invalid mutation attempts |
| UI-side API connection failures | `"ERROR" "ui.src.data_service"` | Signals the API is unreachable from the UI's perspective |
| S3 errors | `"ERROR" "api.src.s3_service"` | Non-`NoSuchKey` S3 failures (upload/download) |

`rental_id`/`reservation_id`/`device_id` in a log line's `extra` fields are what an on-call engineer
uses to pivot from an alarm-linked log line to every other log line touching that entity, and
`username` identifies which user triggered a UI-side event.
