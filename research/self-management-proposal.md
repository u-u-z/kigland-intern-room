# Intern Room 自我管理机制调研报告

## 当前问题诊断

### 1. 今天发现的问题
| 问题 | 根因 | 影响 |
|------|------|------|
| 10:00 小时报告遗漏 | 并发任务时优先级判断错误 | 状态反馈断裂 |
| HEARTBEAT.md 配置过时 | 没有定期审查机制 | 跟踪信息不准确 |
| Issue 状态不同步 | #12-15 已关闭但配置未更新 | 误判任务状态 |
| 工作区变更未提交 | 本地工作区无远程配置 | 配置变更可能丢失 |

### 2. 架构缺陷
```
当前模式:
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ OpenClaw    │────▶│  Agent      │────▶│ GitHub      │
│ Cron Jobs   │     │  (Me)       │     │ Issues      │
└─────────────┘     └─────────────┘     └─────────────┘
       │
       ▼
┌─────────────┐
│ ~/.openclaw │  ◀── 配置分散，无版本控制
│ /workspace  │
└─────────────┘
```

问题：
- 配置分散在两个位置（workspace + intern-room）
- 没有自检机制
- 依赖人工（Remi）发现异常

---

## 自我管理机制设计方案

### 方案 A: 配置集中化 + 自检脚本

```
目标架构:
┌─────────────────────────────────────────────────────────┐
│                   Intern Room (GitHub)                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ .github/    │  │ hooks/      │  │ scripts/    │     │
│  │ workflows/  │  │ self-check/ │  │ health/     │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│                   OpenClaw Agent                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  Pull       │  │  Run        │  │  Report     │     │
│  │  Config     │  │  Checks     │  │  Status     │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

#### 1. 配置集中化

所有配置移入 intern-room 仓库：

```
intern-room/
├── .github/
│   └── workflows/
│       └── health-check.yml      # GitHub Actions 健康检查
├── hooks/
│   ├── README.md
│   ├── triggers.md
│   ├── self-check/               # 新增：自检配置
│   │   ├── heartbeat-config.md   # 心跳检查清单
│   │   ├── cron-manifest.json    # Cron 任务清单
│   │   └── alert-rules.md        # 告警规则
│   └── playbooks/
│       └── daily-ops.md          # 日常运维手册
└── scripts/
    └── health/
        ├── check-issues.sh       # Issues 状态检查
        ├── verify-cron.sh        # Cron 任务验证
        └── report-generator.sh   # 报告生成
```

#### 2. 自检机制

**每小时自检：**
```bash
#!/bin/bash
# scripts/health/hourly-check.sh

echo "## $(date +%H:%M) 自检报告"
echo ""
echo "### Cron 任务状态"
cron status

echo ""
echo "### GitHub Issues"
gh issue list --label "status:ready" --state open
git issue list --label "status:triage" --state open

echo ""
echo "### 工作区状态"
git status --short
git log --oneline -3

echo ""
echo "### 检查点"
echo "- [ ] 小时报告已发送"
echo "- [ ] Issues 状态已确认"
echo "- [ ] 无未提交变更"
```

**每日自检：**
- 审查所有 `wip` Issues 是否有进展
- 检查是否有长期停滞的任务
- 生成日报

#### 3. 告警机制

| 级别 | 条件 | 动作 |
|------|------|------|
| P0 | 小时报告连续遗漏 2 次 | 立即通知 Remi |
| P0 | 发现 `ready` Issue 未处理 > 1h | 立即通知 Remi |
| P1 | 工作区有未提交变更 > 4h | 提醒提交 |
| P1 | Issue 状态与配置不符 | 提醒更新配置 |
| P2 | 日志文件过大 | 自动清理 |

#### 4. 持续改进

**每周回顾：**
```markdown
## Weekly Self-Review

### 本周执行统计
- 小时报告: X/168 (目标 100%)
- 巡检任务: X/2016 (目标 100%)
- 遗漏事件: X 次

### 改进建议
- [ ] Issue 1
- [ ] Issue 2

### 配置变更
- [ ] 需要更新 HEARTBEAT.md?
- [ ] 需要新增检查项?
```

---

### 方案 B: GitHub Actions 增强

利用 GitHub 原生自动化：

```yaml
# .github/workflows/health-check.yml
name: Health Check
on:
  schedule:
    - cron: '0 * * * *'  # 每小时
  workflow_dispatch:

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Check Issues Status
        run: |
          gh issue list --label "status:ready" --state open
          gh issue list --label "status:triage" --state open
      
      - name: Verify Cron Jobs
        run: |
          # 调用 OpenClaw API 检查 cron 状态
          curl -s $OPENCLAW_API/cron/status
      
      - name: Report
        if: failure()
        uses: actions/notify@v1
        with:
          message: "Health check failed"
```

---

## 推荐实施方案

### 立即执行（今天）

1. **修复配置同步问题**
   - 将 `~/.openclaw/workspace/HEARTBEAT.md` 软链接到 `intern-room/hooks/self-check/`
   - 或设置 GitHub Actions 自动同步

2. **添加自检脚本**
   ```bash
   # intern-room/scripts/health/self-check.sh
   # 每小时运行，检查：
   # - 上个小时报告是否发送
   # - Issues 状态
   # - 工作区变更
   ```

3. **更新 Cron 任务**
   - 添加自检任务，每小时执行
   - 设置告警阈值

### 本周完成

1. **建立配置清单**
   - `hooks/self-check/cron-manifest.json` - 记录所有 cron 任务
   - `hooks/self-check/health-checklist.md` - 健康检查清单

2. **完善告警规则**
   - P0: 立即通知
   - P1: 每日汇总
   - P2: 静默记录

### 本月优化

1. **自动化周报生成**
2. **趋势分析**（任务完成率、响应时间）
3. **预测性告警**（基于历史模式）

---

## 具体行动建议

### 选项 1: 保守方案（推荐）
- 保持现有架构
- 添加 `scripts/health/` 自检脚本
- 每小时自检并报告

### 选项 2: 激进方案
- 配置全部移入 intern-room
- 使用 GitHub Actions 作为主要触发器
- OpenClaw 只作为执行器

### 选项 3: 混合方案
- 关键配置在 intern-room
- 运行时配置在 workspace
- 双向同步机制

---

## 需要决策的问题

1. **配置存放位置**：全部集中到 intern-room，还是保持分散？
2. **告警级别**：什么情况下需要立即通知你？
3. **自主性边界**：我可以自主修复问题，还是必须等待确认？
4. **日报内容**：除了系统状态，还需要包含什么？

请指示优先实施哪个方案。
