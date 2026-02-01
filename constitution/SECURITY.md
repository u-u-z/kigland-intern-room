# Constitution: Security

This repo is public. Assume everything here is readable by anyone.

## Hard rules
- No secrets (keys/tokens/cookies/DB URLs with passwords).
- No customer PII.

## Skill/automation rules
- New skills: stage → diff → audit → approval → enable.
- Prefer least privilege.
- Keep an audit trail in Issues + commits.

## If something leaks
- Rotate immediately.
- Rewrite git history if needed.
- File an Incident issue with timeline + remediation.
