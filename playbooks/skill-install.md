# Playbook: Skill install (safe)

## Goal
Install or update a skill without getting pwned.

## Steps
1) Source verification
- Prefer official docs / high-trust sources.

2) Stage
- Download to a staging directory first.
- Review diffs.

3) Static audit
- Look for: `.env`, `Authorization`, `Bearer`, `webhook`, install hooks.

4) Approve
- Human approval required for enabling.

5) Enable + record
- Enable skill.
- Record changes + rationale.

6) Post-check
- Verify behavior.
- Monitor outbound destinations.
