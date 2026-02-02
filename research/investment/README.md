# Investment Ecosystem Intelligence

投资生态情报系统 - 监测早期投资事件，发现潜在机会

---

## 🚀 快速开始

### 单次运行 (生成今日报告)
```bash
python3 scripts/investment-tracker-v2.py --run-once --mock --report
```

### 持续运行模式 (守护进程)
```bash
python3 scripts/investment-tracker-v2.py --daemon --interval 60
```

---

## 📁 项目结构

```
research/investment/
├── daily-reports/          # 每日投资简报
├── weekly-analysis.md      # 周度趋势分析
├── opportunity-alerts.md   # 机会预警
├── investment.db           # SQLite 数据库
├── PHASE1-SUMMARY.md       # Phase 1 摘要
├── PHASE2-SUMMARY.md       # Phase 2 摘要
└── README.md               # 本文件

scripts/
├── investment-tracker.py      # 基础脚本 (Phase 1)
└── investment-tracker-v2.py   # 增强脚本 (Phase 2) ⭐
```

---

## 📊 核心功能

### 1. 数据采集
- ✅ 多数据源采集 (RSS/API/模拟)
- ✅ 智能关键词匹配
- ✅ 自动去重存储

### 2. 报告生成
- ✅ 每日简报自动生成
- ✅ 周度趋势分析
- ✅ 优先级分类 (P0/P1/P2)

### 3. 机会预警
- ✅ 高优先级事件预警
- ✅ 潜在合作机会识别
- ✅ 竞争风险提示

### 4. 重点监测领域
- **MiraclePlus 批次**: 奇绩创坛投资动态
- **AI Agent**: 初创公司融资追踪
- **二次元文化**: Kigurumi、Cosplay 相关投资

---

## 🔧 配置说明

### 关键词配置
编辑 `scripts/investment-tracker.config.py`:
```python
KEYWORDS_CONFIG = {
    'ai': {
        'keywords': ['AI', 'Agent', '大模型', ...],
        'weight': 10
    },
    'niche': {
        'keywords': ['Kigurumi', '二次元', ...],
        'weight': 6
    }
}
```

### 数据源配置
```python
SOURCES = {
    '36kr_rss': {'enabled': True, ...},
    'jingdata': {'enabled': False, ...}  # 需 API Key
}
```

---

## 📈 当前数据

```
数据库统计:
├── 总事件数: 9
├── 近7天事件: 4
├── 近30天事件: 9
└── 高优先级事件: 9

重点领域:
├── AI Agent: 3 个事件
├── 二次元: 3 个事件
└── MiraclePlus: 2 个事件
```

---

## 📝 使用方法

### 生成每日简报
```bash
# 自动生成并保存到 daily-reports/YYYY-MM-DD.md
python3 scripts/investment-tracker-v2.py --run-once --report
```

### 查看数据库统计
```bash
# 查看数据库中的投资事件
sqlite3 research/investment/investment.db "SELECT * FROM funding_events ORDER BY match_score DESC;"
```

### 导出数据
```bash
# 导出为 JSON
python3 scripts/investment-tracker.py --mock --export
```

---

## 🔔 预警规则

当前预警触发条件:

| 条件 | 当前值 | 阈值 | 状态 |
|------|--------|------|------|
| MiraclePlus 相关/周 | 0.5 | >2 | 🟢 正常 |
| AI Agent 融资/周 | 0.5 | >3 | 🟢 正常 |
| 二次元融资/周 | 0.5 | >2 | 🟢 正常 |

---

## 🛠️ 开发计划

### Phase 1 ✅ 已完成
- 数据源研究
- 基础监测脚本
- 数据库存储

### Phase 2 ✅ 已完成
- 持续追踪脚本
- 每日简报系统
- 周度趋势分析
- 机会预警系统

### Phase 3 📋 计划中
- [ ] 接入真实数据源 (鲸准、IT桔子)
- [ ] 自动化通知 (邮件/Telegram)
- [ ] 数据可视化看板
- [ ] LLM 智能分析

---

## 📚 相关文档

- [Phase 1 摘要](PHASE1-SUMMARY.md)
- [Phase 2 摘要](PHASE2-SUMMARY.md)
- [今日简报](daily-reports/2026-02-02.md)
- [周度分析](weekly-analysis.md)
- [机会预警](opportunity-alerts.md)

---

## ⚠️ 注意事项

1. **数据延迟**: RSS 数据源可能有延迟，建议接入真实 API
2. **模拟数据**: 当前部分数据为模拟生成，仅用于演示
3. **API 配置**: 使用 `--no-mock` 前需配置相应 API Key

---

*最后更新: 2026-02-02*
