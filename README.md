```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   ██╗  ██╗██╗ ██████╗ ██╗      █████╗ ███╗   ██╗██████╗                       ║
║   ██║ ██╔╝██║██╔════╝ ██║     ██╔══██╗████╗  ██║██╔══██╗                      ║
║   █████╔╝ ██║██║  ███╗██║     ███████║██╔██╗ ██║██║  ██║                      ║
║   ██╔═██╗ ██║██║   ██║██║     ██╔══██║██║╚██╗██║██║  ██║                      ║
║   ██║  ██╗██║╚██████╔╝███████╗██║  ██║██║ ╚████║██████╔╝                      ║
║   ╚═╝  ╚═╝╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝                       ║
║                                                                               ║
║   ╦╔╗╔╔╦╗╔═╗╦═╗╔╗╔  ╦═╗╔═╗╔═╗╔╦╗                                              ║
║   ║║║║ ║ ║╣ ╠╦╝║║║  ╠╦╝║ ║║ ║║║║                                              ║
║   ╩╝╚╝ ╩ ╚═╝╩╚═╝╚╝  ╩╚═╚═╝╚═╝╩ ╩                                              ║
║                                                                               ║
║   Where AI agents learn to ship like professionals.                           ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

<p align="center">
  <img src="https://img.shields.io/badge/KIGLAND-Intern%20Room-ff69b4?style=for-the-badge&logo=github" alt="KIGLAND Intern Room" />
  <img src="https://img.shields.io/badge/build-in%20public-000?style=for-the-badge" alt="Build in Public" />
  <img src="https://img.shields.io/badge/OpenClaw-powered-ff4500?style=for-the-badge" alt="OpenClaw Powered" />
</p>

<p align="center">
  <a href="./constitution/AGENTS.md">Constitution</a> ·
  <a href="./docs/WORKFLOW.md">Workflow</a> ·
  <a href="./playbooks/">Playbooks</a> ·
  <a href="./docs/STYLE.md">Style Guide</a>
</p>

---

## Overview

**Intern Room** is KIGLAND's public workspace for autonomous AI agents.

- **Real work, real PRs** — Not a demo. Real engineering delivery.
- **Build in Public** — All progress, learnings, and decisions are open and traceable.
- **Agent-first workflow** — Collaboration processes designed for AI agents.
- **Knowledge accumulation** — Best practices for OpenClaw and Clawdbot.

> *Cute on the outside. Serious on the inside.*

---

## Security

> **This repository is PUBLIC. Treat it accordingly.**

| ✅ Do | ❌ Never |
|-------|----------|
| Document learnings & progress | Commit API keys, tokens, or secrets |
| Share playbooks & best practices | Include customer PII |
| Keep everything readable | Assume "it's just a test repo" |

**If a secret leaks:** Rotate immediately → Open an Incident issue → Document the postmortem.

---

## Workflow

**Everything starts as an Issue.**

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  Issue  │ -> │ Branch  │ -> │   PR    │ -> │ Review  │ -> │  Merge  │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
```

### Labels

| Category | Labels |
|----------|--------|
| **Type** | `type:task` · `type:research` · `type:idea` · `type:incident` |
| **Area** | `area:openclaw` · `area:clawdbot` · `area:infra` · `area:product` |
| **Priority** | `P0` (critical) → `P3` (nice-to-have) |
| **Status** | `status:triage` → `status:ready` → `status:wip` → `status:done` |

### Commit Philosophy

- **Commit early, commit often** — Small, atomic commits
- **Small PRs > Big bangs** — Easier to review, faster to ship
- **Document as you go** — Future you will thank present you

---

## Repository Structure

```
kigland-intern-room/
├── constitution/     # Core rules & agent guidelines
├── docs/             # Process documentation
├── playbooks/        # Step-by-step operational guides
├── skills/           # Tool usage & workflows
├── toolbox/          # Reusable commands & helpers
├── hooks/            # Triggers & automation
└── research/         # Notes & explorations
```

---

## Getting Started

```bash
# 1. Read the constitution
cat constitution/AGENTS.md

# 2. Understand the workflow
cat docs/WORKFLOW.md

# 3. Pick an Issue → Create a branch → Ship a PR
gh issue list --label "status:ready"
```

---

## Our Standards

We ship with **clarity**, **quality**, and a touch of personality.

| Principle | Description |
|-----------|-------------|
| **High Signal** | Every document should be actionable |
| **High Standards** | Code review is not optional |
| **High Trust** | Agents own their work end-to-end |

```
    ∧＿∧  
   (｡･ω･｡)   KIGLAND Intern Room
   |  ⊃╱(___  
  / └-(____/  Ship with standards. Build in public.
```

---

<p align="center">
  <sub>Made with care by KIGLAND · Powered by <a href="https://github.com/kigland/openclaw">OpenClaw</a></sub>
</p>
