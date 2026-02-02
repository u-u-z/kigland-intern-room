# Kigurumi Market Intelligence - Heartbeat Tasks

Phase 2 持续监测运营的心跳任务配置

## 执行频率
- 检查间隔: 每 30 分钟

## 任务清单

### 1. 社区数据采集 (每 30 分钟)
```bash
cd /home/remi/.openclaw/workspace && python3 scripts/kigurumi-continuous-monitor.py --once
```

### 2. 每日报告生成 (每天 00:00)
- 自动生成 `research/kigurumi/daily-reports/report_YYYY-MM-DD.md`
- 包含活跃度分析、用户画像、市场趋势

### 3. 竞品情报更新 (每 6 小时)
```bash
cd /home/remi/.openclaw/workspace && python3 scripts/kigurumi-competitor-tracker.py
```

### 4. 数据备份 (每天 02:00)
- 备份 `research/kigurumi/community-data/` 到安全位置
- 保留最近 30 天数据

## 文件状态检查

每次心跳检查以下文件更新:
- [ ] `research/kigurumi/daily-reports/` - 今日报告已生成
- [ ] `research/kigurumi/community-data/messages.jsonl` - 数据持续增长
- [ ] `research/kigurumi/competitor-intel/` - 竞品情报已更新

## 异常处理

如果发现以下情况，发送通知:
1. 连续 2 小时无新数据采集
2. 磁盘空间不足 (剩余 < 1GB)
3. 竞品出现重大动态 (如 Dollkii 发布新品)

## 输出目录

```
research/kigurumi/
├── daily-reports/          # 每日报告
│   ├── report_2026-02-02.md
│   └── report_2026-02-02.json
├── community-data/         # 原始数据
│   ├── messages.jsonl
│   ├── competitor_intel.jsonl
│   └── stats.json
├── competitor-intel/       # 竞品情报
│   └── alert_YYYYMMDD.md
├── user-personas.md        # 用户画像
└── competitor-tracking.md  # 竞品追踪
```
