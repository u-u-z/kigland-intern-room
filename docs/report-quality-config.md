# Report Quality Configuration System

## 概述

本配置定义每日情报报告的质量标准和生成规则。通过调整配置，可控制报告的详细程度、分析深度和可执行性。

## 质量等级 (Quality Tiers)

### Tier-0: Minimal (极简)
**适用场景：** 快速扫描，无重要事件

| 维度 | 要求 |
|------|------|
| 执行摘要 | 3-5 bullet points |
| 数据表格 | ≤2 个 |
| 深度分析 | 无 |
| 行动清单 | 无 |
| 字数 | 300-500 字 |
| 生成时间 | < 30 秒 |

**触发条件：**
- 无 P0/P1 警报
- HN AI 相关故事 < 5
- 无突破性论文

---

### Tier-1: Standard (标准)
**适用场景：** 正常工作日，有值得关注的内容

| 维度 | 要求 |
|------|------|
| 执行摘要 | 表格形式，含优先级和影响评估 |
| 数据表格 | 3-5 个 |
| 深度分析 | 1-2 个重点项目的详细解析 |
| 行动清单 | 3-5 项，按时间分类 |
| 字数 | 800-1,200 字 |
| 生成时间 | < 2 分钟 |

**必须包含：**
- [ ] P0/P1 警报详细说明
- [ ] HN 热门故事列表（points > 100）
- [ ] GitHub trending 分析
- [ ] 对 KIGLAND 的启示（每个重点项目）

---

### Tier-2: Executive Analysis (执行分析)
**适用场景：** 有重大信号或 P1 以上警报

| 维度 | 要求 |
|------|------|
| 执行摘要 | 优先级矩阵（影响 vs 证据强度）|
| 数据表格 | 6-10 个 |
| 深度分析 | ≥3 个重点项目的详细解析 |
| 行动清单 | 按时间分类，明确负责人 |
| 字数 | 1,500-2,500 字 |
| 生成时间 | < 5 分钟 |

**必须包含：**
- [ ] 论文/技术的核心方法解析（非仅标题）
- [ ] 可信度评估（作者背景、代码可用性、社区验证）
- [ ] 量化指标对比（今日 vs 昨日 vs 上周）
- [ ] 趋势判断和预测
- [ ] KIGLAND 直接影响的商业分析

---

### Tier-3: Strategic Deep Dive (战略深度)
**适用场景：** 重大模型发布、行业结构性变化、竞争对手重大动作

| 维度 | 要求 |
|------|------|
| 执行摘要 | 战略机会/威胁评估矩阵 |
| 数据表格 | 10+ 个 |
| 深度分析 | 所有重点项目 + 交叉影响分析 |
| 行动清单 | 详细项目计划（负责人/截止时间/验收标准）|
| 字数 | 3,000-5,000 字 |
| 生成时间 | < 15 分钟 |

**必须包含：**
- [ ] 技术实现的详细解析
- [ ] 竞品对比分析（3+ 家）
- [ ] 市场影响预测（6-12 个月）
- [ ] KIGLAND 战略定位建议
- [ ] 风险与机会矩阵

---

## 报告结构模板

### 标准章节

```
1. Executive Summary (执行摘要)
   - 优先级矩阵
   - 今日最大信号（1句话）
   - 关键数据一览

2. Deep Dive: P0/P1 Alerts (深度分析)
   - 技术核心方法
   - 可信度评估
   - 社区验证状态
   - KIGLAND 影响分析

3. Ecosystem Analysis (生态分析)
   - 信号强度量化
   - 关键项目解析
   - 趋势判断

4. Competitive Intelligence (竞争情报)
   - 竞品动态
   - 市场定位分析

5. Action Items (行动清单)
   - 立即执行（24h）
   - 本周内（7d）
   - 持续监控

6. Trend Comparison (趋势对比)
   - 今日 vs 昨日 vs 上周
   - 变化趋势判断
```

---

## 质量检查清单 (Quality Checklist)

### 内容质量
- [ ] 每个数据点都有来源标注
- [ ] 每个结论都有证据支撑
- [ ] 技术解析准确（非标题党）
- [ ] 影响评估具体到 KIGLAND 业务

### 可执行性
- [ ] 行动清单有明确负责人
- [ ] 截止时间是具体日期
- [ ] 验收标准可量化
- [ ] 优先级排序清晰

### 可读性
- [ ] 表格 > 段落（数据优先）
- [ ] bullet points 不超过 3 层嵌套
- [ ] 关键信息高亮（加粗/颜色）
- [ ] 专业术语有解释

---

## 自动质量评估指标

```json
{
  "quality_score": {
    "data_density": "数据表格数 / 总字数",
    "actionability": "明确负责人和时间的行动项 / 总行动项",
    "depth_score": "深度分析段落数 / 总段落数",
    "kigland_relevance": "提及 KIGLAND 的段落数 / 总段落数"
  },
  "thresholds": {
    "tier_0": {"data_density": 0.01, "actionability": 0, "depth_score": 0.1},
    "tier_1": {"data_density": 0.03, "actionability": 0.5, "depth_score": 0.2},
    "tier_2": {"data_density": 0.05, "actionability": 0.8, "depth_score": 0.3},
    "tier_3": {"data_density": 0.08, "actionability": 1.0, "depth_score": 0.5}
  }
}
```

---

## 配置示例

### 当前配置 (2026-02-05 调整后)

```json
{
  "default_tier": "tier_1",
  "alert_thresholds": {
    "p0": "tier_3",
    "p1": "tier_2",
    "p2": "tier_1"
  },
  "auto_upgrade": {
    "hn_ai_stories": 5,
    "github_trending_ai": 3,
    "breakthrough_papers": 1
  },
  "required_sections": {
    "tier_1": ["summary", "alerts", "github_trends", "action_items"],
    "tier_2": ["summary", "deep_dive", "ecosystem", "competitive", "action_items", "trends"],
    "tier_3": ["all_sections"]
  }
}
```

---

## 更新日志

| 日期 | 变更 | 原因 |
|------|------|------|
| 2026-02-05 | 创建 Tier-2 详细标准 | 用户反馈报告质量下降 |
| 2026-02-05 | 增加质量检查清单 | 确保可执行性 |
| 2026-02-05 | 增加自动质量评估指标 | 量化报告质量 |

---

*Configuration Version: 1.0*  
*Last Updated: 2026-02-05*  
*Owner: RemiBot Intelligence System*
