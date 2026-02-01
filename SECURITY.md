# SECURITY

## Hard rules
- **No secrets in git. Ever.** (API keys, tokens, cookies, credentials, DB URLs with passwords)
- If a secret is committed: **rotate immediately** and rewrite history.
- Do not store customer PII in this repo.

## Safe patterns
- Use environment variables or a secret manager.
- Keep sensitive operational notes out of public repos.
