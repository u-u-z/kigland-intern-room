# Trigger policy

## Trigger sources
- Heartbeat poll
- Cron schedule
- External event (webhook)

## Focus rules
- Do not spam.
- Prefer batching.
- Only alert humans on P0/P1 items.

## P0 examples
- Secret leak suspected
- Unauthorized access
- Gateway exposed publicly

## P1 examples
- Daily research digest
- Weekly status report

## P2 examples
- Update indexes
- Refresh cached lists
