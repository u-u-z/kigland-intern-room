# Hooks

Hooks define when agents should do work without being explicitly prompted.

## Levels
- **P0**: immediate notify (security/production incidents)
- **P1**: periodic summaries (daily/weekly)
- **P2**: silent maintenance (logs, indexes)

## Where things live
- `heartbeat/` — periodic checklists (best-effort cadence)
- `cron/` — schedule-driven tasks (precise timing)
- `events/` — external triggers / webhooks (future)
