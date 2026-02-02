# GitHub Trends 持续调研系统

## 📁 目录结构

```
research/github-trends/
├── README.md                    # 本文件
├── config.json                  # 配置和技术栈定义
├── collect.sh                   # 每日采集脚本
├── weekly-summary.sh            # 每周汇总脚本
├── 2026-02-02.md               # 每日报告示例
└── weekly-summary-YYYY-MM-DD.md # 周报告
```

## 🚀 使用方法

### 每日采集

手动执行：
```bash
cd research/github-trends
./collect.sh
```

或通过 OpenClaw 执行：
```
执行 GitHub Trends 调研任务
```

### 每周汇总

```bash
./weekly-summary.sh
```

## ⚙️ 配置说明

编辑 `config.json` 可自定义：
- 关注的技术栈
- 监控的编程语言
- 相关的关键词标签

## 📊 报告格式

### 每日报告 (YYYY-MM-DD.md)
- 热门项目列表
- KIGLAND 相关项目筛选
- 趋势观察笔记

### 每周报告 (weekly-summary-YYYY-MM-DD.md)
- 一周趋势汇总
- 重点项目分析
- 技术采用建议

## 🕐 执行计划

- **每日**: 10:00 和 22:00 各执行一次
- **每周**: 周日生成周报

## 🔧 技术实现

- 数据来源: GitHub REST API
- 采集工具: curl + jq
- 报告格式: Markdown
