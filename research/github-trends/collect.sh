#!/bin/bash
# GitHub Trends 采集脚本
# 用于每日采集 GitHub 热门项目

set -e

# 配置
RESEARCH_DIR="/home/remi/.openclaw/workspace/research/github-trends"
DATE=$(date +%Y-%m-%d)
DATETIME=$(date '+%Y-%m-%d %H:%M:%S')
REPORT_FILE="$RESEARCH_DIR/$DATE.md"

# 确保目录存在
mkdir -p "$RESEARCH_DIR"

echo "🚀 开始采集 GitHub Trends - $DATETIME"

# 创建报告头部
cat > "$REPORT_FILE" << EOF
# GitHub Trends 调研报告

**采集日期**: $DATE  
**采集时间**: $DATETIME  
**数据来源**: GitHub API

---

## 📊 热门项目概览

EOF

# 采集 Python 热门项目
echo "📦 采集 Python 项目..."
echo "### 🐍 Python 热门项目" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

curl -s "https://api.github.com/search/repositories?q=language:python&sort=stars&order=desc&per_page=10" \
  -H "Accept: application/vnd.github.v3+json" 2>/dev/null | \
  jq -r '.items[] | "- **\(.full_name)** - ⭐ \(.stargazers_count | tostring)  
  - 描述: \(.description // "N/A")  
  - 语言: \(.language // "N/A")  
  - 链接: \(.html_url)  "' 2>/dev/null >> "$REPORT_FILE" || echo "- 数据获取受限" >> "$REPORT_FILE"

echo "" >> "$REPORT_FILE"

# 采集 JavaScript 热门项目
echo "📦 采集 JavaScript 项目..."
echo "### 🟨 JavaScript 热门项目" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

curl -s "https://api.github.com/search/repositories?q=language:javascript&sort=stars&order=desc&per_page=10" \
  -H "Accept: application/vnd.github.v3+json" 2>/dev/null | \
  jq -r '.items[] | "- **\(.full_name)** - ⭐ \(.stargazers_count | tostring)  
  - 描述: \(.description // "N/A")  
  - 语言: \(.language // "N/A")  
  - 链接: \(.html_url)  "' 2>/dev/null >> "$REPORT_FILE" || echo "- 数据获取受限" >> "$REPORT_FILE"

echo "" >> "$REPORT_FILE"

# 采集 TypeScript 热门项目
echo "📦 采集 TypeScript 项目..."
echo "### 📘 TypeScript 热门项目" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

curl -s "https://api.github.com/search/repositories?q=language:typescript&sort=stars&order=desc&per_page=10" \
  -H "Accept: application/vnd.github.v3+json" 2>/dev/null | \
  jq -r '.items[] | "- **\(.full_name)** - ⭐ \(.stargazers_count | tostring)  
  - 描述: \(.description // "N/A")  
  - 语言: \(.language // "N/A")  
  - 链接: \(.html_url)  "' 2>/dev/null >> "$REPORT_FILE" || echo "- 数据获取受限" >> "$REPORT_FILE"

echo "" >> "$REPORT_FILE"

# 添加 KIGLAND 相关项目筛选说明
cat >> "$REPORT_FILE" << EOF

---

## 🎯 KIGLAND 技术栈相关项目

KIGLAND 可能关注的技术领域：
- **Web 开发**: React, Vue, Next.js, Node.js
- **AI/ML**: TensorFlow, PyTorch, Transformers, LLM
- **工具链**: Docker, Kubernetes, CI/CD
- **数据库**: PostgreSQL, MongoDB, Redis
- **云服务**: AWS, Azure, GCP 相关工具

### 相关项目筛选

*基于以上技术栈的热门项目筛选需要手动完成，建议关注：*
1. 与现有项目技术栈匹配度
2. 项目活跃度和维护状态
3. 社区参与度和文档质量

---

## 📝 调研笔记

### 值得关注的趋势
- [待填写]

### 潜在采用的技术
- [待填写]

### 下一步行动
- [ ] 深入调研特定项目
- [ ] 测试关键技术组件
- [ ] 更新技术栈文档

---

*报告由 GitHub Trends 采集脚本自动生成*
EOF

echo "✅ 报告已生成: $REPORT_FILE"
