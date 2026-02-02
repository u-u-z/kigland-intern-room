# 投资事件数据库 Schema

## 表结构

### 1. funding_events (融资事件表)

存储所有采集到的投资事件数据。

```sql
CREATE TABLE funding_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,           -- 公司名称
    funding_round TEXT,                    -- 融资轮次
    amount TEXT,                           -- 融资金额 (原始文本)
    amount_usd REAL,                       -- 美元金额 (估算)
    currency TEXT DEFAULT 'CNY',           -- 币种
    funding_date DATE,                     -- 融资日期
    investors TEXT,                        -- 投资机构 (JSON数组)
    description TEXT,                      -- 事件描述
    source_url TEXT,                       -- 来源链接
    source_platform TEXT,                  -- 来源平台
    tags TEXT,                             -- 标签 (JSON数组)
    keyword_matches TEXT,                  -- 匹配的关键词 (JSON)
    match_score INTEGER DEFAULT 0,         -- 匹配分数
    event_hash TEXT UNIQUE,                -- 事件唯一哈希 (用于去重)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**索引**
```sql
CREATE INDEX idx_funding_date ON funding_events(funding_date);
CREATE INDEX idx_company ON funding_events(company_name);
CREATE INDEX idx_match_score ON funding_events(match_score);
```

### 2. companies (公司信息表)

存储公司详细信息。

```sql
CREATE TABLE companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,             -- 公司名称
    industry TEXT,                         -- 行业
    sub_industry TEXT,                     -- 细分行业
    location TEXT,                         -- 所在地
    description TEXT,                      -- 公司描述
    website TEXT,                          -- 官网
    founded_date DATE,                     -- 成立时间
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 示例数据

### 融资事件

```json
{
  "id": 1,
  "company_name": "DeepAgent AI",
  "funding_round": "种子轮",
  "amount": "100万美元",
  "amount_usd": 1000000,
  "currency": "USD",
  "funding_date": "2026-01-20",
  "investors": "[\"MiraclePlus\", \"红杉种子\"]",
  "description": "构建企业级AI Agent平台",
  "source_url": "https://36kr.com/p/345678",
  "source_platform": "36kr_rss",
  "tags": "[\"人工智能\", \"孵化器\"]",
  "keyword_matches": "[\"人工智能\", \"孵化器\"]",
  "match_score": 28,
  "event_hash": "31d0cd70c86df97124a784818c2ce0d7"
}
```

## 匹配分数计算

匹配分数基于关键词权重累加：

| 类别 | 权重 | 说明 |
|------|------|------|
| 早期投资 | 10 | 天使轮、种子轮等 |
| 人工智能 | 10 | AI、大模型等 |
| 孵化器 | 8 | MiraclePlus、奇绩创坛 |
| 二次元文化 | 6 | Kigurumi、Cosplay |
| 知名机构 | 5 | 红杉、IDG等 |

**高优先级**: score >= 20  
**中优先级**: score >= 10  
**低优先级**: score < 10

## 常用查询

### 最近30天高优先级事件
```sql
SELECT * FROM funding_events 
WHERE funding_date >= date('now', '-30 days') 
  AND match_score >= 20
ORDER BY match_score DESC, funding_date DESC;
```

### 按平台统计
```sql
SELECT source_platform, COUNT(*) as count 
FROM funding_events 
GROUP BY source_platform;
```

### 热门投资机构
```sql
-- 需要解析 investors JSON 字段
SELECT investors, COUNT(*) as count 
FROM funding_events 
GROUP BY investors 
ORDER BY count DESC 
LIMIT 10;
```

---

*Schema Version: 1.0*
