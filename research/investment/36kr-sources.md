# 36Kr (36氪) 投资数据采集方案

## 1. 数据源概述

### 1.1 主要数据源

| 平台 | 类型 | URL | 状态 | 备注 |
|------|------|-----|------|------|
| **36Kr 主站** | 网页/API | https://36kr.com | 🔴 困难 | 有字节跳动验证码保护 |
| **鲸准 (JingData)** | API | https://www.jingdata.com | 🟡 需登录 | 36Kr旗下专业投融资平台 |
| **36Kr RSS** | RSS | https://36kr.com/feed | 🟢 可用 | 内容更新较慢 |
| **Crunchbase** | API/网页 | https://www.crunchbase.com | 🟢 可用 | 国际数据源，补充国内数据 |
| **IT桔子** | API/网页 | https://www.itjuzi.com | 🟡 需登录 | 国内投资数据库 |

### 1.2 数据类型对比

| 数据维度 | 36Kr主站 | 鲸准 | IT桔子 | Crunchbase |
|---------|---------|------|--------|-----------|
| 融资事件 | ✅ 详细 | ✅ 详细 | ✅ 详细 | ⚠️ 有限 |
| 公司信息 | ✅ 完整 | ✅ 完整 | ✅ 完整 | ✅ 完整 |
| 投资机构 | ✅ 完整 | ✅ 详细 | ✅ 详细 | ⚠️ 有限 |
| 投资人物 | ⚠️ 部分 | ✅ 详细 | ✅ 详细 | ❌ 无 |
| 行业分类 | ✅ 详细 | ✅ 详细 | ✅ 详细 | ⚠️ 基础 |
| 实时性 | ✅ 高 | ✅ 高 | ✅ 中 | ⚠️ 低 |

## 2. 数据获取方式分析

### 2.1 36Kr 主站

**技术架构**
- 前端：React SPA (单页应用)
- 反爬：字节跳动 SecSDK 验证码 (滑动验证)
- 数据格式：JSON API

**API 端点 (需绕开验证)**
```
# 快讯 API
https://36kr.com/api/newsflash?b_id=&per_page=20

# 搜索 API  
https://36kr.com/api/search-column/mainsite

# 文章详情
https://36kr.com/api/post/{id}
```

**反爬策略**
1. 使用 Puppeteer/Playwright 模拟浏览器
2. 设置合理的请求间隔 (5-10秒)
3. 使用代理池轮换 IP
4. 保存 cookies 和 localStorage 保持会话

### 2.2 鲸准 (JingData)

**API 端点**
```
# 需要登录 Token
https://www.jingdata.com/api/company/search
https://www.jingdata.com/api/funding/search
https://www.jingdata.com/api/investor/search
```

**数据覆盖**
- 80万+ 创业项目
- 5万+ 实名认证投资人
- 覆盖国内75%以上股权投资机构
- 7000万+ 公司数据

### 2.3 RSS 订阅源

**36Kr RSS 地址**
```
https://36kr.com/feed
```

**优点**
- 无需认证
- 结构稳定
- 无需处理 JavaScript

**缺点**
- 更新频率较低
- 内容摘要不完整
- 无投资数据结构化信息

## 3. 推荐采集策略

### 3.1 多层采集架构

```
┌─────────────────────────────────────────────────────────┐
│                    数据采集层                            │
├─────────────┬─────────────┬─────────────┬───────────────┤
│  36Kr 主站   │   鲸准 API   │   RSS 订阅   │  Crunchbase  │
│  (Playwright)│  (需账号)    │  (feedparser)│  (API/爬虫)   │
└─────────────┴─────────────┴─────────────┴───────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                   数据清洗与去重层                       │
│              (公司名称标准化、事件去重)                   │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                   数据存储层                             │
│              (SQLite / PostgreSQL)                      │
└─────────────────────────────────────────────────────────┘
```

### 3.2 关键词监测策略

**监测关键词列表**

| 类别 | 关键词 | 优先级 |
|------|--------|--------|
| **融资阶段** | 天使轮、种子轮、Pre-A轮、A轮 | P0 |
| **AI领域** | AI初创、大模型、LLM、Agent、人工智能 | P0 |
| **孵化器** | MiraclePlus、奇绩创坛、Y Combinator | P1 |
| **细分领域** | Kigurumi、二次元、Cosplay、ACG | P2 |
| **投资机构** | 红杉、IDG、高瓴、源码资本 | P1 |

**匹配规则**
```python
KEYWORDS = {
    'early_stage': ['天使轮', '种子轮', 'Pre-A轮', '天使+', '种子+'],
    'ai': ['AI', '人工智能', '大模型', 'LLM', 'Agent', 'AIGC', '机器学习'],
    'accelerator': ['MiraclePlus', '奇绩创坛', 'Y Combinator', 'YC China'],
    'niche': ['Kigurumi', '二次元', 'Cosplay', 'ACG', '动漫'],
    'vc_firms': ['红杉', 'IDG', '高瓴', '源码', '五源', 'GGV']
}
```

## 4. 技术实现建议

### 4.1 绕过 36Kr 验证码方案

**方案一：Playwright + 打码平台**
```python
# 使用 Playwright 模拟浏览器
# 遇到验证码时调用打码平台 (如 2captcha、超级鹰)
# 成本：约 ¥0.01-0.05 / 次验证
```

**方案二：逆向 SecSDK**
- 分析 JavaScript 指纹生成逻辑
- 模拟生成合法 fingerprint
- 难度高，需持续维护

**方案三：RSS + 第三方数据源**
- 优先使用 RSS 获取基础内容
- 结合 IT桔子、鲸准 API 补充投资数据
- 最稳定但数据完整度较低

### 4.2 推荐的混合策略

1. **主要数据源**：鲸准 API (需申请账号/开发者权限)
2. **补充数据源**：IT桔子 + Crunchbase (中国公司)
3. **实时监测**：36Kr RSS + 邮件订阅
4. **定期全量**：每月手动导出或购买数据服务

## 5. 数据字段设计

### 5.1 融资事件表 (funding_events)

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键 |
| company_name | TEXT | 公司名称 |
| funding_round | TEXT | 融资轮次 |
| amount | TEXT | 融资金额 |
| amount_usd | REAL | 美元金额 (估算) |
| currency | TEXT | 币种 (CNY/USD) |
| date | DATE | 融资日期 |
| investors | JSON | 投资机构列表 |
| source_url | TEXT | 来源链接 |
| source_platform | TEXT | 来源平台 |
| tags | JSON | 标签 (AI/早期等) |
| created_at | TIMESTAMP | 记录创建时间 |

### 5.2 公司信息表 (companies)

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键 |
| name | TEXT | 公司名称 |
| industry | TEXT | 行业 |
| sub_industry | TEXT | 细分行业 |
| location | TEXT | 所在地 |
| description | TEXT | 简介 |
| website | TEXT | 官网 |
| founded_date | DATE | 成立时间 |

## 6. 法律与合规

### 6.1 数据采集规范

- ✅ 遵守 robots.txt 协议
- ✅ 设置合理的请求频率 (≤ 1 req/sec)
- ✅ 仅采集公开可见信息
- ✅ 不得爬取用户隐私数据

### 6.2 数据使用声明

- 采集的数据仅供个人研究分析使用
- 不得用于商业转售
- 尊重数据来源平台的版权声明

## 7. 后续优化方向

1. **接入付费 API**：鲸准、IT桔子企业版 API
2. **NLP 增强**：使用 LLM 提取非结构化文本中的投资信息
3. **预警系统**：设置关键词提醒，新融资事件自动通知
4. **数据可视化**：搭建看板展示投资趋势

---

*报告生成时间：2026-02-02*
*版本：v1.0*
