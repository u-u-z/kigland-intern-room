# Hooks

Hooks define when agents should do work without being explicitly prompted.

## Levels
- **P0**: immediate notify (security/production incidents)
- **P1**: periodic summaries (daily/weekly)
- **P2**: silent maintenance (logs, indexes)

## Current Files
- `triggers.md` — trigger policy (P0/P1/P2 examples, focus rules)

## Hook Configuration
Hooks are configured in:
- **Heartbeat**: `clawd/HEARTBEAT.md` (agent state machine, issue polling)
- **Cron**: System cron or external scheduler

See `triggers.md` for trigger policy details.
