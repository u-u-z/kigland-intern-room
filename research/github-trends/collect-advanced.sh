#!/bin/bash
# GitHub Trends 高级采集脚本
# 支持 KIGLAND 技术栈的智能筛选

set -e

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESEARCH_DIR="$SCRIPT_DIR"
CONFIG_FILE="$RESEARCH_DIR/config.json"
DATE=$(date +%Y-%m-%d)
DATETIME=$(date '+%Y-%m-%d %H:%M:%S')
REPORT_FILE="$RESEARCH_DIR/$DATE.md"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# 确保目录存在
mkdir -p "$RESEARCH_DIR"

log_info "🚀 开始采集 GitHub Trends - $DATETIME"

# 检查依赖
if ! command -v jq &> /dev/null; then
    log_warn "jq 未安装，尝试使用 apt 安装..."
    sudo apt-get update && sudo apt-get install -y jq
fi

# 创建报告头部
cat > "$REPORT_FILE" << 'HEADER'
# GitHub Trends 调研报告

**采集日期**: REPLACE_DATE  
**采集时间**: REPLACE_DATETIME  
**数据来源**: GitHub API

---

## 📊 热门项目概览

HEADER

# 替换占位符
sed -i "s/REPLACE_DATE/$DATE/g" "$REPORT_FILE"
sed -i "s/REPLACE_DATETIME/$DATETIME/g" "$REPORT_FILE"

# 采集函数
fetch_github_repos() {
    local language=$1
    local count=${2:-10}
    
    log_info "📦 采集 $language 项目..."
    
    local response
    response=$(curl -s "https://api.github.com/search/repositories?q=language:$language&sort=stars&order=desc&per_page=$count" \
        -H "Accept: application/vnd.github.v3+json" 2>/dev/null)
    
    if echo "$response" | jq -e '.items' > /dev/null 2>&1; then
        echo "$response" | jq -r '.items[] | select(.stargazers_count > 1000) | "- **\(.full_name)** - ⭐ \(.stargazers_count | tostring)
  - 描述: \(.description // "N/A")
  - 语言: \(.language // "N/A")
  - 链接: \(.html_url)"'
    else
        log_warn "$language 数据获取失败或受限"
        echo "- 数据获取受限，请稍后重试"
    fi
}

# 采集 AI/ML 项目
fetch_ai_repos() {
    local query=$1
    local label=$2
    local count=${3:-10}
    
    log_info "🤖 采集 $label 项目..."
    
    local response
    response=$(curl -s "https://api.github.com/search/repositories?q=$query&sort=stars&order=desc&per_page=$count" \
        -H "Accept: application/vnd.github.v3+json" 2>/dev/null)
    
    if echo "$response" | jq -e '.items' > /dev/null 2>&1; then
        echo "$response" | jq -r '.items[] | select(.stargazers_count > 500) | "- **\(.full_name)** - ⭐ \(.stargazers_count | tostring)
  - 描述: \(.description // "N/A")
  - 语言: \(.language // "N/A")
  - 链接: \(.html_url)"'
    else
        log_warn "$label 数据获取失败或受限"
        echo "- 数据获取受限，请稍后重试"
    fi
}

# 采集各语言项目
echo "" >> "$REPORT_FILE"
echo "### 🐍 Python 热门项目" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
fetch_github_repos "python" 10 >> "$REPORT_FILE"

echo "" >> "$REPORT_FILE"
echo "### 🟨 JavaScript 热门项目" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
fetch_github_repos "javascript" 10 >> "$REPORT_FILE"

echo "" >> "$REPORT_FILE"
echo "### 📘 TypeScript 热门项目" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
fetch_github_repos "typescript" 10 >> "$REPORT_FILE"

echo "" >> "$REPORT_FILE"
echo "### 🤖 AI/ML 热门项目" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
fetch_ai_repos "topic:machine-learning" "Machine Learning" 8 >> "$REPORT_FILE"

echo "" >> "$REPORT_FILE"
echo "### 🧠 LLM / AI Agent 热门项目" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
fetch_ai_repos "LLM+OR+LangChain+OR+autogpt" "LLM/AI Agent" 8 >> "$REPORT_FILE"

# 添加 KIGLAND 相关分析
cat >> "$REPORT_FILE" << 'ANALYSIS'

---

## 🎯 KIGLAND 技术栈相关项目分析

### 🔥 高相关度项目

#### AI/ML 领域
- **huggingface/transformers** - LLM 和 NLP 领域的核心库
- **langchain-ai/langchain** - LLM 应用开发框架
- **Significant-Gravitas/AutoGPT** - 自主 AI Agent
- **pytorch/pytorch** - 深度学习框架

#### Web 开发领域
- **vercel/next.js** - React 全栈框架
- **facebook/react** - UI 库
- **shadcn-ui/ui** - 现代化 UI 组件
- **nestjs/nest** - 后端 Node.js 框架

#### 工具链
- **n8n-io/n8n** - 工作流自动化
- **prisma/prisma** - 现代化 ORM
- **apache/airflow** - 工作流调度

### 💡 推荐关注

| 项目 | 相关度 | 用途 | 优先级 |
|------|--------|------|--------|
| langchain | 高 | LLM 应用开发 | ⭐⭐⭐ |
| next.js | 高 | 全栈 Web 开发 | ⭐⭐⭐ |
| shadcn-ui/ui | 高 | UI 组件库 | ⭐⭐⭐ |
| n8n | 中 | 工作流自动化 | ⭐⭐ |
| prisma | 中 | 数据库 ORM | ⭐⭐ |

ANALYSIS

# 添加趋势观察
cat >> "$REPORT_FILE" << 'TRENDS'

---

## 📝 今日趋势观察

### 值得关注的新趋势
- [待填写]

### 技术方向建议
- **短期**: [待分析]
- **中期**: [待分析]
- **长期**: [待分析]

---

*报告由 GitHub Trends 采集脚本自动生成*
*下次采集时间: 今日 22:00 或明日 10:00*
TRENDS

log_success "✅ 报告已生成: $REPORT_FILE"
log_info "📄 文件大小: $(du -h "$REPORT_FILE" | cut -f1)"
