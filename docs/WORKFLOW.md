# Workflow

We run this repo like a serious organization: clarity, traceability, and repeatability.

## 1) Everything is an Issue
Create an Issue for:
- Tasks to execute
- Ideas to explore
- Research questions
- Bugs/incidents

## 2) Classification (labels)
Use labels to route work:

**Type**
- `type:task` — concrete deliverable
- `type:research` — reading/learning + extracted best practices
- `type:idea` — proposals / experiments
- `type:incident` — security/availability problems

**Area**
- `area:openclaw` — OpenClaw runtime/config
- `area:clawdbot` — skills/plugins/tools
- `area:infra` — servers, networking, deploy
- `area:product` — KIGLAND product/ops

**Priority**
- `P0` / `P1` / `P2` / `P3`

**Status**
- `status:triage` / `status:ready` / `status:wip` / `status:blocked` / `status:done`

## 3) Branch + PR
- Branch naming: `intern/<short-topic>` or `feat/<topic>`
- PR should link the Issue: `Fixes #123`
- Keep PRs small; ship iteratively.

## 4) Commit discipline
- Commit early, commit often.
- Commit message style:
  - `type(scope): summary`
  - Examples:
    - `docs(openclaw): add model provider notes`
    - `playbooks(security): add skill install checklist`

## 5) Definition of Done (DoD)
A task is done when:
- Notes are written to `research/` or `docs/`
- Repro steps exist (commands / configs)
- Risks & mitigations are recorded (security, cost, maintenance)
- Issue updated with outcome + next steps
