#!/bin/bash
# GitHub Trends 每周汇总脚本
# 汇总一周的热门项目生成周报

set -e

RESEARCH_DIR="/home/remi/.openclaw/workspace/research/github-trends"
WEEK_START=$(date -d "last monday" +%Y-%m-%d 2>/dev/null || date -v-Mon +%Y-%m-%d)
WEEK_END=$(date +%Y-%m-%d)
REPORT_FILE="$RESEARCH_DIR/weekly-summary-$WEEK_START-to-$WEEK_END.md"

echo "📝 生成周报: $WEEK_START 至 $WEEK_END"

# 获取本周的所有日报文件
DAILY_REPORTS=$(ls -1 $RESEARCH_DIR/2026-*.md 2>/dev/null | sort || echo "")

cat > "$REPORT_FILE" << EOF
# GitHub Trends 周报

**报告周期**: $WEEK_START 至 $WEEK_END  
**生成时间**: $(date '+%Y-%m-%d %H:%M:%S')

---

## 📊 本周概览

### 热门语言趋势
- Python: [分析待填]
- JavaScript/TypeScript: [分析待填]
- AI/ML 相关: [分析待填]

### 本周新星项目
1. [待分析]

---

## 📈 详细数据

### 每日报告列表
EOF

# 列出本周的每日报告
for report in $DAILY_REPORTS; do
    filename=$(basename "$report")
    echo "- [$filename](./$filename)" >> "$REPORT_FILE"
done

cat >> "$REPORT_FILE" << EOF

---

## 🎯 KIGLAND 技术栈关注点

### 高优先级项目
*本周发现的高度相关项目*

### 采用建议
1. [待填写]

### 技术债务关注
- [待填写]

---

## 🔮 趋势预测

### 下月可能流行的技术
- [待分析]

### 需要持续跟踪的项目
- [待填写]

---

*周报由 GitHub Trends 采集系统自动生成*
EOF

echo "✅ 周报已生成: $REPORT_FILE"
