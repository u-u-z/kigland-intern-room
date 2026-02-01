# GitHub (gh) snippets

## List org repos
```bash
gh repo list ORG --limit 50
```

## Create issue
```bash
gh issue create --repo owner/repo --title "..." --body "..."
```

## Add labels
```bash
gh issue edit 123 --add-label "type:task" --repo owner/repo
```
